from flask import Flask, render_template, request, redirect, url_for
from flask.json.provider import DefaultJSONProvider
import os
import pandas as pd
import numpy as np
from analytics import analyze_finances, load_sample_data
from file_parsers import parse_file
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from os import getenv
import user_store
try:
    from azure.identity import DefaultAzureCredential
    from azure.keyvault.secrets import SecretClient
    AZURE_AVAILABLE = True
except Exception:
    AZURE_AVAILABLE = False


# Custom JSON encoder to handle numpy/pandas types
class CustomJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif pd.isna(obj):
            return None
        return super().default(obj)


app = Flask(__name__)
app.json = CustomJSONProvider(app)

# Load secret key: prefer Key Vault via Managed Identity if configured
secret = getenv('APP_SECRET_KEY')
kv_url = getenv('KEYVAULT_URL')  # e.g., https://<your-key-vault-name>.vault.azure.net/
kv_secret_name = getenv('KEYVAULT_APP_SECRET_NAME', 'APP_SECRET_KEY')
if not secret and AZURE_AVAILABLE and kv_url:
    try:
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=kv_url, credential=credential)
        secret = client.get_secret(kv_secret_name).value
    except Exception:
        secret = None

app.secret_key = secret or 'dev-secret-change-me'
login_manager = LoginManager(app)
login_manager.login_view = 'login'

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'data', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize database
user_store.init_db()


class User(UserMixin):
    def __init__(self, id, email):
        self.id = id
        self.email = email


@login_manager.user_loader
def load_user(user_id):
    user = user_store.get_user_by_email(user_id)
    if user:
        return User(id=user['email'], email=user['email'])
    return None


@app.route('/')
@login_required
def index():
    # Load sample data for the landing demo
    tx_df, acct_df = load_sample_data()
    results = analyze_finances(tx_df, acct_df)
    return render_template('dashboard.html', results=results)


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        tx_file = request.files.get('transactions')
        acct_file = request.files.get('accounts')
        if not tx_file or not acct_file:
            return render_template('upload.html', error='Please provide both files.')

        try:
            # Read file contents
            tx_content = tx_file.read()
            acct_content = acct_file.read()
            
            # Parse files based on their format
            tx_df = parse_file(tx_content, tx_file.filename, file_type='transactions')
            acct_df = parse_file(acct_content, acct_file.filename, file_type='accounts')
            
            # Validate required columns
            required_tx_cols = ['date', 'amount', 'type']
            required_acct_cols = ['balance', 'type']
            
            if not all(col in tx_df.columns for col in required_tx_cols):
                return render_template('upload.html', 
                    error=f'Transactions file must contain columns: {", ".join(required_tx_cols)}')
            
            if not all(col in acct_df.columns for col in required_acct_cols):
                return render_template('upload.html', 
                    error=f'Accounts file must contain columns: {", ".join(required_acct_cols)}')
            
            # Run analysis
            results = analyze_finances(tx_df, acct_df)
            return render_template('dashboard.html', results=results)
            
        except ValueError as e:
            return render_template('upload.html', error=str(e))
        except Exception as e:
            return render_template('upload.html', 
                error=f'Error processing files: {str(e)}. Please check file format.')

    return render_template('upload.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user_data = user_store.verify_user(email, password)
        if user_data:
            user = User(id=user_data['email'], email=user_data['email'])
            login_user(user)
            return redirect(url_for('index'))
        return render_template('login.html', error='Invalid credentials.')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        
        if not email or not password:
            return render_template('register.html', error='Email and password required.')
        if password != confirm:
            return render_template('register.html', error='Passwords do not match.')
        if len(password) < 8:
            return render_template('register.html', error='Password must be at least 8 characters.')
        
        user = user_store.create_user(email, password)
        if user:
            return redirect(url_for('login', registered=1))
        return render_template('register.html', error='Email already registered.')
    return render_template('register.html')


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        token = user_store.create_reset_token(email)
        if token:
            # In production, send email with reset link
            reset_link = url_for('reset_password', token=token, _external=True)
            return render_template('forgot_password.html', 
                                 success=f'Reset link (demo): {reset_link}')
        return render_template('forgot_password.html', 
                             error='If email exists, reset link will be sent.')
    return render_template('forgot_password.html')


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        
        if password != confirm:
            return render_template('reset_password.html', token=token, 
                                 error='Passwords do not match.')
        if len(password) < 8:
            return render_template('reset_password.html', token=token, 
                                 error='Password must be at least 8 characters.')
        
        if user_store.reset_password(token, password):
            return redirect(url_for('login', reset=1))
        return render_template('reset_password.html', token=token, 
                             error='Invalid or expired token.')
    
    # Verify token is valid
    if not user_store.verify_reset_token(token):
        return render_template('reset_password.html', token=token, 
                             error='Invalid or expired token.')
    return render_template('reset_password.html', token=token)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/account/export')
@login_required
def export_data():
    """Export user data (GDPR compliance)."""
    from flask import jsonify
    data = user_store.export_user_data(current_user.email)
    return jsonify(data)


@app.route('/account/delete', methods=['POST'])
@login_required
def delete_account():
    """Delete user account (GDPR compliance)."""
    email = current_user.email
    logout_user()
    user_store.delete_user_account(email)
    return redirect(url_for('login', deleted=1))


@app.route('/health')
def health():
    """Health check endpoint for monitoring."""
    return {'status': 'healthy', 'service': 'finance-diagnostics'}, 200


if __name__ == '__main__':
    app.run(debug=True, port=5001)
