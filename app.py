from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify, session, send_from_directory
from flask.json.provider import DefaultJSONProvider
import os
import pandas as pd
import numpy as np
from analytics import analyze_finances, load_sample_data
from file_parsers import parse_file
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from functools import wraps
from flask import abort
from os import getenv
import user_store
import json
from datetime import datetime
import io
import client_manager
try:
    import stripe
    STRIPE_AVAILABLE = True
except Exception:
    STRIPE_AVAILABLE = False
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

# Optional: seed admin from environment variables
ADMIN_EMAIL = getenv('ADMIN_EMAIL')
ADMIN_PASSWORD = getenv('ADMIN_PASSWORD')
if ADMIN_EMAIL and ADMIN_PASSWORD:
    try:
        user_store.create_admin(ADMIN_EMAIL.strip().lower(), ADMIN_PASSWORD)
    except Exception:
        # Seeding admin is best-effort; continue if it fails
        pass

# Stripe configuration (optional; only used if keys are provided)
STRIPE_SECRET_KEY = getenv('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = getenv('STRIPE_PUBLISHABLE_KEY')
STRIPE_PRICE_ID = getenv('STRIPE_PRICE_ID')  # e.g., 'price_1SmcTcEPS0ev8tkiLDa2mJqM'
STRIPE_WEBHOOK_SECRET = getenv('STRIPE_WEBHOOK_SECRET')
STRIPE_CHECKOUT_URL = getenv('STRIPE_CHECKOUT_URL') or 'https://buy.stripe.com/cNi9ATgk4cZRfYW9UE5c401'
if STRIPE_AVAILABLE and STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY


class User(UserMixin):
    def __init__(self, id, email, is_admin=False):
        self.id = id
        self.email = email
        self.is_admin = bool(is_admin)


@login_manager.user_loader
def load_user(user_id):
    user = user_store.get_user_by_email(user_id)
    if user:
        return User(id=user['email'], email=user['email'], is_admin=user.get('is_admin', 0))
    return None


# --- Admin utilities ---
def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if not getattr(current_user, 'is_admin', False):
            abort(403)
        return f(*args, **kwargs)
    return wrapper


@app.route('/')
def landing():
    # Public landing page (no login required)
    return render_template('landing.html', 
                         stripe_publishable_key=STRIPE_PUBLISHABLE_KEY or '',
                         stripe_price_id=STRIPE_PRICE_ID or '')


@app.route('/service-worker.js')
def service_worker_file():
    # Serve SW from root so it controls the whole scope
    return send_from_directory(app.root_path, 'service-worker.js', mimetype='application/javascript')


@app.route('/dashboard')
@login_required
def index():
    # Gate access if user hasn't paid
    if (not getattr(current_user, 'is_admin', False)) and (not user_store.has_paid(current_user.email)):
        return redirect(url_for('paywall'))
    # Empty dashboard — no data loaded until user uploads their own file
    results = {
        'income': 0.0,
        'expenses': 0.0,
        'savings_rate': 0.0,
        'alerts': [],
        'recommendations': [],
        'benchmarks': {'your_savings_rate': 0.0, 'age_group_average': 12.0},
        'overspending': [],
        'charts': {
            'income_vs_expenses': {'labels': ['Income', 'Expenses'], 'data': [0.0, 0.0]},
            'category_breakdown': {'labels': [], 'data': []},
            'savings_progress': {'liquid_savings': 0.0, 'target_emergency': 0.0},
            'monthly_trends': {'months': [], 'income': [], 'expenses': [], 'savings': []},
        },
        'monthly_trends': {'months': [], 'income': [], 'expenses': [], 'savings': []},
        'prediction': None,
        'recurring_transactions': [],
        'category_trends': [],
        'unusual_transactions': [],
        'optimization': {},
        'diagnostic_report': {},
        'no_data': True,
    }
    return render_template('dashboard_enhanced.html', results=results)


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        tx_file = request.files.get('transactions')
        acct_file = request.files.get('accounts')
        if not tx_file:
            return render_template('upload.html', error='Please provide a transactions file.', questionnaire_complete=bool(session.get('questionnaire_responses', {})))

        try:
            # Read file contents
            tx_content = tx_file.read()
            acct_content = acct_file.read() if acct_file else None

            # Parse transactions
            tx_df = parse_file(tx_content, tx_file.filename, file_type='transactions')
            # Normalize transaction columns: lowercase, strip, simple slug
            def _norm(name):
                return ''.join(ch if ch.isalnum() else '_' for ch in str(name).strip().lower())
            tx_df.columns = [_norm(c) for c in tx_df.columns]

            # Helper to robustly parse amounts (handles decimal comma and currency symbols)
            def _to_num_series(s):
                s = s.astype(str).str.replace('\u00a0', '', regex=False).str.replace(' ', '', regex=False)
                s = s.str.replace('€', '', regex=False).str.replace('$', '', regex=False)
                # If string has commas and no dots, treat comma as decimal separator
                def _fix(val):
                    v = str(val)
                    if v.count(',') == 1 and v.count('.') == 0:
                        v = v.replace(',', '.')
                    else:
                        # remove thousand separators
                        v = v.replace(',', '')
                    return v
                s = s.apply(_fix)
                return pd.to_numeric(s, errors='coerce')

            # Derive/normalize required columns
            # date
            if 'date' not in tx_df.columns:
                for alt in ['transaction_date', 'transactiondate', 'posted_date', 'post_date', 'postingdate', 'valuedate', 'value_date', 'date_time', 'datetime']:
                    if alt in tx_df.columns:
                        tx_df['date'] = tx_df[alt]
                        break
            # amount
            if 'amount' not in tx_df.columns:
                cols = set(tx_df.columns)
                # Common alternates: debit/credit or money_in/out or deposit/withdrawal
                if {'debit', 'credit'}.issubset(cols):
                    tx_df['amount'] = _to_num_series(tx_df['credit']).fillna(0) - _to_num_series(tx_df['debit']).fillna(0)
                elif {'money_in', 'money_out'}.issubset(cols):
                    tx_df['amount'] = _to_num_series(tx_df['money_in']).fillna(0) - _to_num_series(tx_df['money_out']).fillna(0)
                elif {'moneyin', 'moneyout'}.issubset(cols):
                    tx_df['amount'] = _to_num_series(tx_df['moneyin']).fillna(0) - _to_num_series(tx_df['moneyout']).fillna(0)
                elif {'credit_amount', 'debit_amount'}.issubset(cols):
                    tx_df['amount'] = _to_num_series(tx_df['credit_amount']).fillna(0) - _to_num_series(tx_df['debit_amount']).fillna(0)
                elif {'cr_amount', 'dr_amount'}.issubset(cols):
                    tx_df['amount'] = _to_num_series(tx_df['cr_amount']).fillna(0) - _to_num_series(tx_df['dr_amount']).fillna(0)
                elif {'deposit', 'withdrawal'}.issubset(cols):
                    tx_df['amount'] = _to_num_series(tx_df['deposit']).fillna(0) - _to_num_series(tx_df['withdrawal']).fillna(0)
                elif 'value' in cols:
                    tx_df['amount'] = _to_num_series(tx_df['value'])
                elif 'transaction_amount' in cols:
                    tx_df['amount'] = _to_num_series(tx_df['transaction_amount'])
            # type
            if 'type' not in tx_df.columns:
                if 'dc' in tx_df.columns:  # debit/credit marker (e.g., 'D'/'C')
                    tx_df['type'] = tx_df['dc'].astype(str).str.upper().map({'C': 'income', 'CR': 'income', 'D': 'expense', 'DR': 'expense'})
                elif 'dr_cr' in tx_df.columns:
                    tx_df['type'] = tx_df['dr_cr'].astype(str).str.upper().map({'CR': 'income', 'DR': 'expense'})
                elif 'amount' in tx_df.columns:
                    tx_df['type'] = _to_num_series(tx_df['amount']).fillna(0).apply(lambda x: 'income' if x > 0 else 'expense')
            else:
                tx_df['type'] = tx_df['type'].astype(str).str.lower()

            # description
            if 'description' not in tx_df.columns:
                found = False
                for alt in ['details', 'narrative', 'memo', 'reference', 'description1', 'transaction_description']:
                    if alt in tx_df.columns:
                        tx_df['description'] = tx_df[alt]
                        found = True
                        break
                if not found:
                    # Fallback default
                    tx_df['description'] = 'Unknown'

            # category
            if 'category' not in tx_df.columns:
                tx_df['category'] = 'Uncategorized'

            # If still missing required columns, try heuristic inference from generic tables
            required_tx_cols = ['date', 'amount', 'type']
            missing_pre = [c for c in required_tx_cols if c not in tx_df.columns]
            if missing_pre:
                try:
                    from file_parsers import infer_transaction_columns
                    tx_df = infer_transaction_columns(tx_df)
                except Exception:
                    pass

            # Final fallback: compute amount from moneyin/moneyout if present (with or without underscore)
            if 'amount' not in tx_df.columns:
                cset = set(tx_df.columns)
                has_in = 'money_in' in cset or 'moneyin' in cset
                has_out = 'money_out' in cset or 'moneyout' in cset
                if has_in or has_out:
                    money_in_series = None
                    money_out_series = None
                    if 'money_in' in cset:
                        money_in_series = _to_num_series(tx_df['money_in']).fillna(0)
                    elif 'moneyin' in cset:
                        money_in_series = _to_num_series(tx_df['moneyin']).fillna(0)
                    else:
                        money_in_series = pd.Series(0, index=tx_df.index)

                    if 'money_out' in cset:
                        money_out_series = _to_num_series(tx_df['money_out']).fillna(0)
                    elif 'moneyout' in cset:
                        money_out_series = _to_num_series(tx_df['moneyout']).fillna(0)
                    else:
                        money_out_series = pd.Series(0, index=tx_df.index)

                    tx_df['amount'] = money_in_series - money_out_series

            if 'type' not in tx_df.columns and 'amount' in tx_df.columns:
                tx_df['type'] = _to_num_series(tx_df['amount']).fillna(0).apply(lambda x: 'income' if x > 0 else 'expense')

            # Parse accounts or load fallback
            if acct_content:
                acct_df = parse_file(acct_content, acct_file.filename, file_type='accounts')
                acct_df.columns = [str(c).strip().lower() for c in acct_df.columns]
            else:
                # Use sample accounts as fallback
                _, acct_df = load_sample_data()

            # Ensure account columns exist
            if 'balance' not in acct_df.columns:
                acct_df['balance'] = acct_df.get('amount', 0)
            if 'type' not in acct_df.columns:
                acct_df['type'] = acct_df.get('account_type', 'checking')

            # Final validation minimal
            required_tx_cols = ['date', 'amount', 'type']
            missing = [c for c in required_tx_cols if c not in tx_df.columns]
            if missing:
                detected = ', '.join(list(tx_df.columns))
                return render_template('upload.html', 
                    error=f'Could not detect required columns: {", ".join(missing)}. Detected columns: {detected}. If your bank uses different names, share the header row and I will map them.',
                    questionnaire_complete=bool(session.get('questionnaire_responses', {})))

            # Persist transactions to allow export endpoints to work
            try:
                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                save_path = os.path.join(UPLOAD_FOLDER, f"transactions_{ts}.csv")
                tx_df.to_csv(save_path, index=False)
                session['data_file'] = save_path
            except Exception:
                # Non-fatal; continue without persistence
                pass

            # Run analysis
            results = analyze_finances(tx_df, acct_df)
            results['questionnaire'] = session.get('questionnaire_responses', {})
            return render_template('dashboard_enhanced.html', results=results)

        except ValueError as e:
            return render_template('upload.html', error=str(e), questionnaire_complete=bool(session.get('questionnaire_responses', {})))
        except Exception as e:
            return render_template('upload.html', 
                error=f'Error processing files: {str(e)}. Please check file format.',
                questionnaire_complete=bool(session.get('questionnaire_responses', {})))

    if request.method == 'GET':
        session.pop('data_file', None)

    return render_template('upload.html', questionnaire_complete=bool(session.get('questionnaire_responses', {})))


# ---------------------------------------------------------------------------
# Client file management routes
# ---------------------------------------------------------------------------

@app.route('/clients')
@login_required
@admin_required
def clients_list():
    """Admin: list all clients."""
    clients = client_manager.list_clients()
    return render_template('clients.html', clients=clients)


@app.route('/clients/new', methods=['POST'])
@login_required
@admin_required
def clients_new():
    """Admin: create a new client folder."""
    client_name = request.form.get('client_name', '').strip()
    if not client_name:
        clients = client_manager.list_clients()
        return render_template('clients.html', clients=clients, error='Client name is required.')
    result = client_manager.create_client(client_name)
    if not result['ok']:
        clients = client_manager.list_clients()
        return render_template('clients.html', clients=clients, error=result['error'])
    return redirect(url_for('client_detail', client_slug=result['slug']))


@app.route('/clients/<client_slug>')
@login_required
@admin_required
def client_detail(client_slug):
    """Admin: view a client's files."""
    if not client_manager.client_exists(client_slug):
        return redirect(url_for('clients_list'))
    files = client_manager.get_client_files(client_slug)
    return render_template('client_detail.html',
                           client_slug=client_slug,
                           client_name=client_slug.replace('_', ' '),
                           files=files)


@app.route('/clients/<client_slug>/upload', methods=['POST'])
@login_required
@admin_required
def client_upload(client_slug):
    """Admin: upload a file to a client folder and optionally run analysis."""
    if not client_manager.client_exists(client_slug):
        return redirect(url_for('clients_list'))

    uploaded = request.files.get('file')
    if not uploaded or not uploaded.filename:
        files = client_manager.get_client_files(client_slug)
        return render_template('client_detail.html',
                               client_slug=client_slug,
                               client_name=client_slug.replace('_', ' '),
                               files=files,
                               error='No file selected.')

    result = client_manager.save_client_file(client_slug, uploaded, uploaded.filename)
    if not result['ok']:
        files = client_manager.get_client_files(client_slug)
        return render_template('client_detail.html',
                               client_slug=client_slug,
                               client_name=client_slug.replace('_', ' '),
                               files=files,
                               error=result['error'])

    # If user requested analysis, redirect to analyze endpoint
    if request.form.get('analyze'):
        return redirect(url_for('client_analyze', client_slug=client_slug, filename=result['filename']))

    files = client_manager.get_client_files(client_slug)
    return render_template('client_detail.html',
                           client_slug=client_slug,
                           client_name=client_slug.replace('_', ' '),
                           files=files,
                           success=f'File "{result["filename"]}" saved successfully.')


@app.route('/clients/<client_slug>/analyze/<path:filename>')
@login_required
@admin_required
def client_analyze(client_slug, filename):
    """Admin: run financial analysis on a client file and show dashboard."""
    path = client_manager.get_client_file_path(client_slug, filename)
    if not path:
        return redirect(url_for('client_detail', client_slug=client_slug))

    try:
        with open(path, 'rb') as f:
            content = f.read()
        tx_df = parse_file(content, filename, file_type='transactions')
        tx_df.columns = [''.join(ch if ch.isalnum() else '_' for ch in str(c).strip().lower()) for c in tx_df.columns]

        # Minimal column normalization (reuse same logic as /upload)
        def _to_num(s):
            s = s.astype(str).str.replace(r'[\u00a0 €$,]', '', regex=True)
            return pd.to_numeric(s, errors='coerce')

        if 'amount' not in tx_df.columns:
            for pair in [('credit', 'debit'), ('money_in', 'money_out'), ('deposit', 'withdrawal')]:
                if set(pair).issubset(tx_df.columns):
                    tx_df['amount'] = _to_num(tx_df[pair[0]]).fillna(0) - _to_num(tx_df[pair[1]]).fillna(0)
                    break
        if 'type' not in tx_df.columns and 'amount' in tx_df.columns:
            tx_df['type'] = _to_num(tx_df['amount']).fillna(0).apply(lambda x: 'income' if x > 0 else 'expense')
        if 'date' not in tx_df.columns:
            for alt in ['transaction_date', 'posted_date', 'value_date']:
                if alt in tx_df.columns:
                    tx_df['date'] = tx_df[alt]
                    break
        if 'description' not in tx_df.columns:
            for alt in ['details', 'narrative', 'memo', 'reference']:
                if alt in tx_df.columns:
                    tx_df['description'] = tx_df[alt]
                    break
            else:
                tx_df['description'] = 'Unknown'
        if 'category' not in tx_df.columns:
            tx_df['category'] = 'Uncategorized'

        _, acct_df = load_sample_data()
        results = analyze_finances(tx_df, acct_df)
        results['client_name'] = client_slug.replace('_', ' ')
        results['source_file'] = filename
        results['transactions'] = tx_df.to_dict('records')
        return render_template('dashboard_enhanced.html', results=results)
    except Exception as e:
        import traceback
        err = f"Analysis failed: {str(e)}"
        files = client_manager.get_client_files(client_slug)
        return render_template('client_detail.html',
                               client_slug=client_slug,
                               client_name=client_slug.replace('_', ' '),
                               files=files,
                               error=err)


@app.route('/clients/<client_slug>/delete-file', methods=['POST'])
@login_required
@admin_required
def client_delete_file(client_slug):
    """Admin: delete a file from a client folder."""
    filename = request.form.get('filename', '')
    client_manager.delete_client_file(client_slug, filename)
    return redirect(url_for('client_detail', client_slug=client_slug))


@app.route('/clients/<client_slug>/delete', methods=['POST'])
@login_required
@admin_required
def client_delete(client_slug):
    """Admin: delete a client and all their files."""
    client_manager.delete_client(client_slug)
    return redirect(url_for('clients_list'))


@app.route('/clients/<client_slug>/report/<path:filename>')
@login_required
@admin_required
def client_report(client_slug, filename):
    """Admin: download a clean diagnostic report for a client file."""
    path = client_manager.get_client_file_path(client_slug, filename)
    if not path:
        return redirect(url_for('client_detail', client_slug=client_slug))
    try:
        with open(path, 'rb') as f:
            content = f.read()
        tx_df = parse_file(content, filename, file_type='transactions')
        tx_df.columns = [''.join(ch if ch.isalnum() else '_' for ch in str(c).strip().lower()) for c in tx_df.columns]

        def _to_num(s):
            s = s.astype(str).str.replace(r'[\u00a0 €$,]', '', regex=True)
            return pd.to_numeric(s, errors='coerce')

        if 'amount' not in tx_df.columns:
            for pair in [('credit', 'debit'), ('money_in', 'money_out'), ('deposit', 'withdrawal')]:
                if set(pair).issubset(tx_df.columns):
                    tx_df['amount'] = _to_num(tx_df[pair[0]]).fillna(0) - _to_num(tx_df[pair[1]]).fillna(0)
                    break
        if 'type' not in tx_df.columns and 'amount' in tx_df.columns:
            tx_df['type'] = _to_num(tx_df['amount']).fillna(0).apply(lambda x: 'income' if x > 0 else 'expense')
        if 'date' not in tx_df.columns:
            for alt in ['transaction_date', 'posted_date', 'value_date']:
                if alt in tx_df.columns:
                    tx_df['date'] = tx_df[alt]
                    break
        if 'description' not in tx_df.columns:
            for alt in ['details', 'narrative', 'memo', 'reference']:
                if alt in tx_df.columns:
                    tx_df['description'] = tx_df[alt]
                    break
            else:
                tx_df['description'] = 'Unknown'
        if 'category' not in tx_df.columns:
            tx_df['category'] = 'Uncategorized'

        _, acct_df = load_sample_data()
        results = analyze_finances(tx_df, acct_df)

        client_name = client_slug.replace('_', ' ').title()
        html = _generate_html_report(results, client_name=client_name,
                                     source_file=filename, transactions_df=tx_df)
        return html, 200, {'Content-Type': 'text/html; charset=utf-8'}
    except Exception as e:
        err = f"Report generation failed: {str(e)}"
        files = client_manager.get_client_files(client_slug)
        return render_template('client_detail.html',
                               client_slug=client_slug,
                               client_name=client_slug.replace('_', ' '),
                               files=files,
                               error=err)


@app.route('/contract')
def contract():
    return render_template('contract.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user_data = user_store.verify_user(email, password)
        if user_data:
            user = User(id=user_data['email'], email=user_data['email'], is_admin=user_data.get('is_admin', 0))
            login_user(user)
            # Redirect to dashboard instead of index (which is now the landing page)
            if getattr(user, 'is_admin', False):
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('paywall') if not user_store.has_paid(email) else url_for('index'))
        return render_template('login.html', error='Invalid credentials.')
    return render_template('login.html')



@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    """Simple admin dashboard: list users and flags."""
    try:
        users = user_store.list_users()
        rows = ''.join([
            f"<tr><td>{u['email']}</td><td>{u['created_at']}</td><td>{'yes' if u.get('paid') else 'no'}</td><td>{'yes' if u.get('is_admin') else 'no'}</td></tr>"
            for u in users
        ])
        html = (
            "<h2>Admin Dashboard</h2>"
            "<p>Quick links: "
            "<a href='/dashboard'>Open Dashboard</a> | "
            "<a href='/upload'>Upload Files</a> | "
            "<a href='/clients'>Client Files</a> | "
            "<a href='/'>Landing Page</a> | "
            "<a href='/pay'>Paywall</a>"
            "</p>"
            "<table border='1' cellpadding='6'><thead><tr><th>Email</th><th>Created</th><th>Paid</th><th>Admin</th></tr></thead>"
            f"<tbody>{rows}</tbody></table>"
            "<p><a href='/'>&larr; Home</a></p>"
        )
        return html
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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
        
        # Require payment before allowing registration
        if not user_store.has_paid(email):
            return render_template('register.html', error='Please complete payment to create an account.')
        user = user_store.create_user(email, password)
        if user:
            return redirect(url_for('login', registered=1))
        return render_template('register.html', error='Email already registered.')
    return render_template('register.html')


@app.route('/api/register', methods=['POST'])
def api_register():
    """API endpoint for registering a new user"""
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required.'}), 400
    
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters.'}), 400
    
    # Check if user already exists
    existing = user_store.get_user_by_email(email)
    if existing:
        return jsonify({'error': 'Email already registered. Please login.'}), 400
    
    # Create user (unpaid initially, will be marked paid after Stripe webhook)
    user = user_store.create_user(email, password)
    if not user:
        return jsonify({'error': 'Could not create user. Please try again.'}), 500
    
    return jsonify({'success': True, 'message': 'User registered. Redirecting to payment...'}), 201


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


# --- Payments: Stripe Checkout ---
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    """Return or redirect to Stripe checkout."""
    # Prefer explicit hosted link when provided
    if STRIPE_CHECKOUT_URL:
        if request.method == 'POST':
            return jsonify({'checkout_url': STRIPE_CHECKOUT_URL})
        return redirect(STRIPE_CHECKOUT_URL, code=303)

    # Fallback to creating a session dynamically
    if not STRIPE_AVAILABLE:
        return ("Stripe not available. Payment system temporarily unavailable.", 503)
    
    if not STRIPE_SECRET_KEY or not STRIPE_PRICE_ID:
        return ("Stripe not configured. Set STRIPE_SECRET_KEY and STRIPE_PRICE_ID.", 500)

    try:
        success_url = url_for('checkout_success', _external=True) + "?session_id={CHECKOUT_SESSION_ID}"
        cancel_url = url_for('checkout_cancel', _external=True)
        session_obj = stripe.checkout.Session.create(
            mode='payment',
            line_items=[{'price': STRIPE_PRICE_ID, 'quantity': 1}],
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return jsonify({'checkout_url': session_obj.url}) if request.method == 'POST' else redirect(session_obj.url, code=303)
    except Exception as e:
        return (f"Failed to create checkout session: {str(e)}", 500)


@app.route('/checkout/success')
def checkout_success():
    return "Payment successful. You can now register/login to access the beta."


@app.route('/checkout/cancel')
def checkout_cancel():
    return "Payment canceled. No charge was made."


@app.route('/account/export')
@login_required
def export_data():
    """Export user data (GDPR compliance)."""
    data = user_store.export_user_data(current_user.email)
    return jsonify(data)


# ---------------------------------------------------------------------------
# Clean report generator — used by both /api/export/pdf and client reports
# ---------------------------------------------------------------------------

def _generate_clean_report(results: dict, client_name: str = None, source_file: str = None, transactions_df=None) -> str:
    """Return a clean, number-focused diagnostic report as plain text."""
    W = 66  # line width
    bar = '━' * W

    def section(title):
        return f"\n{bar}\n  {title}\n{bar}\n"

    def money(v):
        try:
            return f"€{float(v):>12,.2f}"
        except Exception:
            return f"{'N/A':>13}"

    def pct(v):
        try:
            return f"{float(v):>6.1f}%"
        except Exception:
            return "   N/A"

    lines = []

    # ── Header ──────────────────────────────────────────────────────────────
    lines.append('╔' + '═' * (W - 2) + '╗')
    lines.append('║' + '  FINANCIAL DIAGNOSTIC REPORT'.center(W - 2) + '║')
    if client_name:
        lines.append('║' + f'  Client: {client_name}'.ljust(W - 2) + '║')
    if source_file:
        lines.append('║' + f'  File:   {source_file}'.ljust(W - 2) + '║')
    lines.append('║' + f'  Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")} UTC'.ljust(W - 2) + '║')
    lines.append('╚' + '═' * (W - 2) + '╝')

    # ── Health score ────────────────────────────────────────────────────────
    diag = results.get('diagnostic_report') or {}
    score = diag.get('overall_score', 0)
    grade = diag.get('grade', 'N/A')
    lines.append(section('HEALTH SCORE'))
    lines.append(f"  Score : {score}/100   Grade: {grade}")
    score_desc = (
        'Excellent' if score >= 80 else
        'Good' if score >= 60 else
        'Fair — Room for Improvement' if score >= 40 else
        'Needs Urgent Attention'
    )
    lines.append(f"  Status: {score_desc}")

    # Category scores
    diagnostics = diag.get('diagnostics') or {}
    if diagnostics:
        lines.append('')
        lines.append(f"  {'Category':<22}  {'Score':>5}   {'Status'}")
        lines.append(f"  {'-'*22}  {'-'*5}   {'-'*20}")
        for cat, data in diagnostics.items():
            cat_label = cat.replace('_', ' ').title()
            s = data.get('score', 0)
            st = data.get('status', '').title()
            bar_full = '█' * int(s / 10) + '░' * (10 - int(s / 10))
            lines.append(f"  {cat_label:<22}  {s:>4}/100  {bar_full}  {st}")

    # ── Key numbers ─────────────────────────────────────────────────────────
    income   = results.get('income', 0)
    expenses = results.get('expenses', 0)
    net      = income - expenses
    sav_rate = results.get('savings_rate', 0)
    forecast = (results.get('prediction') or {}).get('predicted_expenses', 0)

    lines.append(section('KEY NUMBERS'))
    lines.append(f"  {'Total Income':<30}  {money(income)}")
    lines.append(f"  {'Total Expenses':<30}  {money(expenses)}")
    lines.append(f"  {'Net (Saved)':<30}  {money(net)}")
    lines.append(f"  {'Savings Rate':<30}  {pct(sav_rate * 100):>13}")
    if forecast:
        lines.append(f"  {'Next Month Forecast':<30}  {money(forecast)}")

    # ── Monthly breakdown ───────────────────────────────────────────────────
    monthly = results.get('monthly_trends') or {}
    months_list = monthly.get('months', [])
    inc_list    = monthly.get('income', [])
    exp_list    = monthly.get('expenses', [])
    sav_list    = monthly.get('savings', [])

    if months_list:
        lines.append(section('MONTHLY BREAKDOWN'))
        lines.append(f"  {'Month':<12}  {'Income':>12}  {'Expenses':>12}  {'Saved':>12}  {'Rate':>7}")
        lines.append(f"  {'-'*12}  {'-'*12}  {'-'*12}  {'-'*12}  {'-'*7}")
        for i, m in enumerate(months_list):
            inc_v = inc_list[i] if i < len(inc_list) else 0
            exp_v = exp_list[i] if i < len(exp_list) else 0
            sav_v = sav_list[i] if i < len(sav_list) else 0
            rate_v = (sav_v / inc_v * 100) if inc_v else 0
            lines.append(
                f"  {str(m):<12}  {money(inc_v)}  {money(exp_v)}  {money(sav_v)}  {pct(rate_v)}"
            )

    # ── Top spending categories ──────────────────────────────────────────────
    overspending = results.get('overspending', [])
    cat_data     = (results.get('charts') or {}).get('category_breakdown') or {}
    cat_labels   = cat_data.get('labels', [])
    cat_amounts  = cat_data.get('data', [])
    total_exp    = max(float(expenses), 1e-9)

    if cat_labels:
        lines.append(section('TOP SPENDING CATEGORIES'))
        lines.append(f"  {'#':<3}  {'Category':<22}  {'Amount':>12}  {'% of Expenses':>14}")
        lines.append(f"  {'-'*3}  {'-'*22}  {'-'*12}  {'-'*14}")
        for rank, (lbl, amt) in enumerate(zip(cat_labels[:10], cat_amounts[:10]), 1):
            pct_v = float(amt) / total_exp * 100
            flag  = '  ⚠ HIGH' if pct_v >= 20 else ''
            lines.append(f"  {rank:<3}  {str(lbl):<22}  {money(amt)}  {pct(pct_v):>14}{flag}")

    # ── Recurring bills ──────────────────────────────────────────────────────
    recurring = results.get('recurring_transactions', [])
    if recurring:
        lines.append(section('RECURRING BILLS & SUBSCRIPTIONS'))
        lines.append(f"  {'Description':<28}  {'Amount':>12}  {'Frequency':<12}  {'Next Due'}")
        lines.append(f"  {'-'*28}  {'-'*12}  {'-'*12}  {'-'*12}")
        total_rec = 0.0
        for r in recurring[:15]:
            desc = str(r.get('description', ''))[:27]
            amt  = r.get('amount', 0)
            freq = str(r.get('frequency', ''))
            due  = str(r.get('next_due', ''))
            lines.append(f"  {desc:<28}  {money(amt)}  {freq:<12}  {due}")
            total_rec += float(amt)
        lines.append(f"  {'─'*28}  {'─'*12}")
        lines.append(f"  {'TOTAL RECURRING':<28}  {money(total_rec)}")

    # ── Alerts ──────────────────────────────────────────────────────────────
    alerts = results.get('alerts', [])
    risks  = diag.get('risks', [])
    if alerts or risks:
        lines.append(section('ALERTS & RISKS'))
        for a in alerts:
            lines.append(f"  ⚠  {a}")
        for r in (risks[:5] if isinstance(risks, list) else []):
            if isinstance(r, dict):
                sev = r.get('severity', 'medium').upper()
                msg = r.get('message', '')
                lines.append(f"  [{sev}]  {msg}")
            elif isinstance(r, str):
                lines.append(f"  ⚠  {r}")

    # ── Recommendations ──────────────────────────────────────────────────────
    recs_basic = results.get('recommendations', [])
    recs_diag  = diag.get('recommendations', [])
    all_recs   = list(recs_diag[:6]) if recs_diag else []
    if not all_recs:
        all_recs = recs_basic

    if all_recs:
        lines.append(section('RECOMMENDATIONS'))
        for i, rec in enumerate(all_recs, 1):
            if isinstance(rec, dict):
                pri    = rec.get('priority', 'medium').upper()
                action = rec.get('action', '')
                impact = rec.get('impact', '')
                lines.append(f"  {i}. [{pri}] {action}")
                if impact:
                    lines.append(f"       → {impact}")
            else:
                lines.append(f"  {i}. {rec}")

    # ── All transactions ─────────────────────────────────────────────────────
    if transactions_df is not None and not transactions_df.empty:
        try:
            tx = transactions_df.copy()
            # Normalize columns
            tx.columns = [''.join(ch if ch.isalnum() else '_' for ch in str(c).strip().lower())
                          for c in tx.columns]
            if 'date' in tx.columns:
                tx['date'] = pd.to_datetime(tx['date'], errors='coerce', dayfirst=True)
                tx = tx.sort_values('date', na_position='last')
            total_tx = len(tx)
            lines.append(section(f'ALL TRANSACTIONS  ({total_tx} total)'))
            lines.append(f"  {'Date':<12}  {'Description':<40}  {'Amount':>10}  {'Type':<8}  {'Category'}")
            lines.append(f"  {'-'*12}  {'-'*40}  {'-'*10}  {'-'*8}  {'-'*20}")
            income_total = 0.0
            expense_total = 0.0
            for _, row in tx.iterrows():
                try:
                    d = str(row.get('date', ''))[:10]
                    desc = str(row.get('description', ''))[:39]
                    amt = float(row.get('amount', 0) or 0)
                    t = str(row.get('type', '')).lower()
                    cat = str(row.get('category', 'Uncategorized'))[:20]
                    sign = '+' if t == 'income' else '-'
                    lines.append(f"  {d:<12}  {desc:<40}  {sign}€{amt:>8,.2f}  {t.capitalize():<8}  {cat}")
                    if t == 'income':
                        income_total += amt
                    else:
                        expense_total += amt
                except Exception:
                    continue
            lines.append(f"  {'─'*12}  {'─'*40}  {'─'*10}  {'─'*8}")
            lines.append(f"  {'TOTAL INCOME':<54}  +€{income_total:>8,.2f}")
            lines.append(f"  {'TOTAL EXPENSES':<54}  -€{expense_total:>8,.2f}")
            lines.append(f"  {'NET':<54}   €{income_total - expense_total:>8,.2f}")
        except Exception:
            pass

    lines.append('')
    lines.append('═' * W)
    lines.append('  This report is generated automatically from your financial data.')
    lines.append('  Consult a certified financial advisor for personalised advice.')
    lines.append('═' * W)

    return '\n'.join(lines)


def _generate_html_report(results: dict, client_name: str = None, source_file: str = None, transactions_df=None) -> str:
    """Return a rich HTML report with Plotly charts — grouped by category, no raw transactions."""
    import json as _json

    income   = float(results.get('income', 0) or 0)
    expenses = float(results.get('expenses', 0) or 0)
    net      = income - expenses
    sav_rate = float(results.get('savings_rate', 0) or 0) * 100
    diag     = results.get('diagnostic_report') or {}
    score    = diag.get('overall_score', 0)
    grade    = diag.get('grade', '—')
    forecast = float((results.get('prediction') or {}).get('predicted_expenses', 0) or 0)

    score_color = '#10b981' if score >= 70 else '#f59e0b' if score >= 50 else '#ef4444'
    net_color   = '#10b981' if net >= 0 else '#ef4444'

    # ── Category totals (grouped, unknowns → Others) ───────────────────────
    UNKNOWN_LABELS = {'uncategorized', 'unknown', 'other', 'others', '', 'nan', 'none'}
    TOP_N = 10  # show top 10, rest → Others

    cat_labels_raw = (results.get('charts') or {}).get('category_breakdown', {}).get('labels', [])
    cat_amounts_raw = (results.get('charts') or {}).get('category_breakdown', {}).get('data', [])

    cat_map = {}
    for lbl, amt in zip(cat_labels_raw, cat_amounts_raw):
        key = str(lbl).strip()
        if key.lower() in UNKNOWN_LABELS:
            key = 'Others'
        cat_map[key] = cat_map.get(key, 0) + float(amt)

    # sort descending, keep top N, rest into Others
    sorted_cats = sorted(cat_map.items(), key=lambda x: x[1], reverse=True)
    if len(sorted_cats) > TOP_N:
        top = sorted_cats[:TOP_N]
        rest = sum(v for _, v in sorted_cats[TOP_N:])
        if rest > 0:
            top.append(('Others', rest))
        sorted_cats = top

    pie_labels = [c[0] for c in sorted_cats]
    pie_values = [round(c[1], 2) for c in sorted_cats]
    total_exp_shown = max(sum(pie_values), 1e-9)

    # ── Monthly trend data ─────────────────────────────────────────────────
    monthly  = results.get('monthly_trends') or {}
    m_months = monthly.get('months', [])
    m_inc    = [float(x) for x in monthly.get('income', [])]
    m_exp    = [float(x) for x in monthly.get('expenses', [])]
    m_sav    = [float(x) for x in monthly.get('savings', [])]

    # ── Recurring ─────────────────────────────────────────────────────────
    recurring = results.get('recurring_transactions', []) or []

    # ── Alerts ─────────────────────────────────────────────────────────────
    alerts = results.get('alerts', []) or []

    # ── Recommendations ────────────────────────────────────────────────────
    recs_diag  = (diag.get('recommendations') or [])
    recs_basic = results.get('recommendations', []) or []
    recs = list(recs_diag[:6]) if recs_diag else recs_basic

    # ── JSON for Plotly ────────────────────────────────────────────────────
    pie_json = _json.dumps({'labels': pie_labels, 'values': pie_values})
    bar_json = _json.dumps({'months': [str(m) for m in m_months], 'income': m_inc, 'expenses': m_exp, 'savings': m_sav})

    # ── Category table rows ────────────────────────────────────────────────
    cat_rows_html = ''
    for rank, (lbl, amt) in enumerate(sorted_cats, 1):
        pct_v = amt / total_exp_shown * 100
        flag = '<span style="color:#ef4444;font-weight:700"> ⚠</span>' if pct_v >= 20 else ''
        bar_w = min(int(pct_v * 2), 100)
        cat_rows_html += f'''
        <tr>
          <td style="padding:0.5rem 0.75rem;color:#6b7280">{rank}</td>
          <td style="padding:0.5rem 0.75rem;font-weight:600">{lbl}{flag}</td>
          <td style="padding:0.5rem 0.75rem;text-align:right;font-weight:700">€{amt:,.2f}</td>
          <td style="padding:0.5rem 0.75rem;text-align:right;color:#6b7280">{pct_v:.1f}%</td>
          <td style="padding:0.5rem 0.75rem;min-width:120px">
            <div style="height:10px;background:#e5e7eb;border-radius:5px">
              <div style="height:10px;width:{bar_w}%;background:linear-gradient(90deg,#667eea,#764ba2);border-radius:5px"></div>
            </div>
          </td>
        </tr>'''

    # ── Recurring rows ────────────────────────────────────────────────────
    rec_rows_html = ''
    total_rec = 0.0
    for r in recurring[:15]:
        desc = str(r.get('description', ''))[:40]
        amt  = float(r.get('amount', 0) or 0)
        freq = str(r.get('frequency', ''))
        due  = str(r.get('next_due', ''))
        total_rec += amt
        rec_rows_html += f'<tr><td style="padding:0.5rem 0.75rem">{desc}</td><td style="padding:0.5rem 0.75rem;text-align:right;font-weight:700">€{amt:,.2f}</td><td style="padding:0.5rem 0.75rem;color:#6b7280">{freq}</td><td style="padding:0.5rem 0.75rem;color:#6b7280">{due}</td></tr>'
    if rec_rows_html:
        rec_rows_html += f'<tr style="border-top:2px solid #e5e7eb;background:#f9fafb"><td style="padding:0.5rem 0.75rem;font-weight:700">TOTAL RECURRING</td><td style="padding:0.5rem 0.75rem;text-align:right;font-weight:700;color:#ef4444">€{total_rec:,.2f}</td><td colspan="2"></td></tr>'

    # Pre-build recurring card (can't nest ''' inside f''')
    if rec_rows_html:
        recurring_card_html = (
            '<div class="card"><h2>\U0001f504 Recurring Bills &amp; Subscriptions</h2>'
            '<table><thead><tr><th>Description</th>'
            '<th style="text-align:right">Amount</th>'
            '<th>Frequency</th><th>Next Due</th></tr></thead>'
            '<tbody>' + rec_rows_html + '</tbody></table></div>'
        )
    else:
        recurring_card_html = ''

    # ── Alerts HTML ────────────────────────────────────────────────────────
    alerts_html = ''.join(
        f'<div style="background:#fef9c3;border-left:4px solid #f59e0b;padding:0.75rem 1rem;border-radius:4px;margin-bottom:0.5rem">⚠️ {a}</div>'
        for a in alerts
    ) if alerts else '<p style="color:#6b7280">No critical alerts.</p>'

    # ── Recs HTML ─────────────────────────────────────────────────────────
    recs_html = ''
    for i, rec in enumerate(recs, 1):
        if isinstance(rec, dict):
            action = rec.get('action', '')
            impact = rec.get('impact', '')
            pri    = rec.get('priority', 'medium').upper()
            pri_color = '#10b981' if pri == 'HIGH' else '#f59e0b'
            recs_html += f'<div style="margin-bottom:0.75rem;padding:0.75rem 1rem;background:#f8f9ff;border-left:4px solid {pri_color};border-radius:4px"><strong>{i}. {action}</strong>'
            if impact:
                recs_html += f'<br><span style="color:#6b7280;font-size:0.9em">→ {impact}</span>'
            recs_html += '</div>'
        else:
            recs_html += f'<div style="margin-bottom:0.5rem;padding:0.75rem 1rem;background:#f8f9ff;border-left:4px solid #667eea;border-radius:4px">{i}. {rec}</div>'
    if not recs_html:
        recs_html = '<p style="color:#6b7280">No recommendations available.</p>'

    generated = datetime.now().strftime('%Y-%m-%d %H:%M')

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Financial Report — {client_name or 'Client'}</title>
  <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
  <style>
    *{{margin:0;padding:0;box-sizing:border-box}}
    body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f5f7fa;color:#1f2937}}
    .page{{max-width:960px;margin:0 auto;padding:2rem 1rem 4rem}}
    .header{{background:linear-gradient(135deg,#667eea,#764ba2);color:white;border-radius:16px;padding:2.5rem;margin-bottom:2rem;text-align:center}}
    .header h1{{font-size:2rem;margin-bottom:0.25rem}}
    .header .sub{{opacity:0.85;font-size:0.95rem}}
    .kpi-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:1rem;margin-bottom:2rem}}
    .kpi{{background:white;border-radius:12px;padding:1.5rem;box-shadow:0 2px 10px rgba(0,0,0,.07);text-align:center}}
    .kpi .label{{font-size:0.8rem;color:#6b7280;text-transform:uppercase;letter-spacing:.05em;margin-bottom:0.5rem}}
    .kpi .value{{font-size:1.8rem;font-weight:800}}
    .kpi .sub{{font-size:0.82rem;color:#9ca3af;margin-top:0.3rem}}
    .card{{background:white;border-radius:12px;padding:1.75rem;box-shadow:0 2px 10px rgba(0,0,0,.07);margin-bottom:2rem}}
    .card h2{{font-size:1.15rem;font-weight:700;color:#374151;margin-bottom:1.25rem;padding-bottom:0.6rem;border-bottom:2px solid #e5e7eb}}
    table{{width:100%;border-collapse:collapse}}
    thead th{{background:#f9fafb;padding:0.6rem 0.75rem;text-align:left;font-size:0.8rem;text-transform:uppercase;color:#6b7280;letter-spacing:.04em}}
    tbody tr:hover{{background:#f9fafb}}
    .charts-grid{{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;margin-bottom:2rem}}
    .print-btn{{position:fixed;bottom:2rem;right:2rem;background:linear-gradient(135deg,#667eea,#764ba2);color:white;border:none;border-radius:50px;padding:0.85rem 1.75rem;font-size:1rem;font-weight:700;cursor:pointer;box-shadow:0 4px 15px rgba(102,126,234,.4)}}
    @media print{{.print-btn{{display:none}};body{{background:white}};.page{{padding:0}};.header{{border-radius:0}}}}
    @media(max-width:600px){{.charts-grid{{grid-template-columns:1fr}};.kpi-grid{{grid-template-columns:1fr 1fr}}}}
  </style>
</head>
<body>
<div class="page">

  <div class="header">
    <h1>💰 Financial Diagnostic Report</h1>
    <div class="sub">{'Client: ' + client_name if client_name else ''} &nbsp;·&nbsp; Generated: {generated}</div>
    {'<div class="sub" style="margin-top:.3rem;font-size:.8rem;opacity:.7">Source: ' + (source_file or '') + '</div>' if source_file else ''}
  </div>

  <!-- KPI cards -->
  <div class="kpi-grid">
    <div class="kpi">
      <div class="label">Total Income</div>
      <div class="value" style="color:#10b981">€{income:,.0f}</div>
    </div>
    <div class="kpi">
      <div class="label">Total Expenses</div>
      <div class="value" style="color:#ef4444">€{expenses:,.0f}</div>
    </div>
    <div class="kpi">
      <div class="label">Net Saved</div>
      <div class="value" style="color:{net_color}">€{net:,.0f}</div>
    </div>
    <div class="kpi">
      <div class="label">Savings Rate</div>
      <div class="value" style="color:{'#10b981' if sav_rate >= 10 else '#ef4444'}">{sav_rate:.1f}%</div>
      <div class="sub">Target 12%</div>
    </div>
    <div class="kpi">
      <div class="label">Health Score</div>
      <div class="value" style="color:{score_color}">{score}<span style="font-size:1rem">/100</span></div>
      <div class="sub">{grade}</div>
    </div>
    {('<div class="kpi"><div class="label">Next Month Forecast</div><div class="value" style="color:#f59e0b">€' + f'{forecast:,.0f}' + '</div></div>') if forecast else ''}
  </div>

  <!-- Charts row -->
  <div class="charts-grid">
    <div class="card" style="margin-bottom:0">
      <h2>🥧 Spending by Category</h2>
      <div id="pie-chart" style="height:320px"></div>
    </div>
    <div class="card" style="margin-bottom:0">
      <h2>📈 Monthly Income vs Expenses</h2>
      <div id="bar-chart" style="height:320px"></div>
    </div>
  </div>
  <div style="margin-bottom:2rem"></div>

  <!-- Category table -->
  <div class="card">
    <h2>📊 Expenses by Category</h2>
    <table>
      <thead><tr><th>#</th><th>Category</th><th style="text-align:right">Amount</th><th style="text-align:right">% of Total</th><th>Share</th></tr></thead>
      <tbody>{cat_rows_html}</tbody>
      <tfoot><tr style="border-top:2px solid #e5e7eb;background:#f9fafb">
        <td colspan="2" style="padding:0.6rem 0.75rem;font-weight:700">TOTAL EXPENSES</td>
        <td style="padding:0.6rem 0.75rem;text-align:right;font-weight:800;color:#ef4444">€{expenses:,.2f}</td>
        <td colspan="2"></td>
      </tr></tfoot>
    </table>
  </div>

  {recurring_card_html}

  <div class="card">
    <h2>⚠️ Alerts</h2>
    {alerts_html}
  </div>

  <div class="card">
    <h2>💡 Recommendations</h2>
    {recs_html}
  </div>

  <div style="text-align:center;color:#9ca3af;font-size:0.82rem;margin-top:2rem">
    This report is generated automatically from your financial data.<br>
    Consult a certified financial advisor for personalised advice.
  </div>

</div>

<button class="print-btn" onclick="window.print()">🖨️ Print / Save as PDF</button>

<script>
const pie = {pie_json};
const bar = {bar_json};

Plotly.newPlot('pie-chart', [{{
  type: 'pie',
  labels: pie.labels,
  values: pie.values,
  hole: 0.4,
  textinfo: 'label+percent',
  textposition: 'outside',
  hovertemplate: '<b>%{{label}}</b><br>€%{{value:,.2f}}<br>%{{percent}}<extra></extra>',
  marker: {{ colors: ['#667eea','#764ba2','#ef4444','#f59e0b','#10b981','#3b82f6','#8b5cf6','#ec4899','#14b8a6','#f97316','#6b7280'] }}
}}], {{
  margin: {{t:10,b:30,l:10,r:10}},
  showlegend: false,
  paper_bgcolor: 'white'
}}, {{responsive: true, displayModeBar: false}});

if (bar.months && bar.months.length > 0) {{
  Plotly.newPlot('bar-chart', [
    {{type:'bar', name:'Income', x:bar.months, y:bar.income, marker:{{color:'#10b981'}}}},
    {{type:'bar', name:'Expenses', x:bar.months, y:bar.expenses, marker:{{color:'#ef4444'}}}},
    {{type:'scatter', name:'Saved', x:bar.months, y:bar.savings, mode:'lines+markers', line:{{color:'#667eea',width:2}}, marker:{{size:6}}}}
  ], {{
    barmode: 'group',
    margin: {{t:10,b:60,l:60,r:10}},
    xaxis: {{tickangle:-30}},
    yaxis: {{tickprefix:'€', tickformat:',.0f'}},
    legend: {{orientation:'h', y:-0.25}},
    paper_bgcolor: 'white',
    plot_bgcolor: '#f9fafb'
  }}, {{responsive: true, displayModeBar: false}});
}} else {{
  document.getElementById('bar-chart').innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#9ca3af">Not enough monthly data</div>';
}}
</script>
</body>
</html>'''
    return html


@app.route('/api/export/data')
@login_required
def api_export_data():
    """Export user financial data as JSON file."""
    try:
        # Get user's uploaded data file path
        data_file = session.get('data_file')
        if not data_file or not os.path.exists(data_file):
            # Use demo data if no file uploaded
            transactions_df, accounts_df = load_sample_data()
        else:
            transactions_df = pd.read_csv(data_file)
            accounts_df = pd.DataFrame()  # Empty if not provided
        
        # Analyze the data
        results = analyze_finances(transactions_df, accounts_df)
        
        # Prepare export data
        export_data = {
            'exported_at': datetime.now().isoformat(),
            'user': current_user.email,
            'transactions_count': len(transactions_df),
            'summary': {
                'total_income': float(results['income']),
                'total_expenses': float(results['expenses']),
                'savings_rate': float(results['savings_rate']),
                'health_score': float(results.get('diagnostic_report', {}).get('overall_score', 0))
            },
            'transactions': transactions_df.to_dict('records'),
            'diagnostic_report': results.get('diagnostic_report', {}),
            'questionnaire_responses': session.get('questionnaire_responses', {})
        }
        
        # Create JSON file in memory
        json_data = json.dumps(export_data, indent=2, default=str)
        buffer = io.BytesIO()
        buffer.write(json_data.encode('utf-8'))
        buffer.seek(0)
        
        # Generate filename with timestamp
        filename = f"financial_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        return send_file(
            buffer,
            mimetype='application/json',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/export/pdf')
@login_required
def api_export_pdf():
    """Download a clean, number-focused financial diagnostic report."""
    try:
        data_file = session.get('data_file')
        if not data_file or not os.path.exists(data_file):
            transactions_df, accounts_df = load_sample_data()
        else:
            transactions_df = pd.read_csv(data_file)
            accounts_df = pd.DataFrame()

        results = analyze_finances(transactions_df, accounts_df)
        report_text = _generate_clean_report(results, client_name=current_user.email)

        buffer = io.BytesIO()
        buffer.write(report_text.encode('utf-8'))
        buffer.seek(0)
        filename = f"diagnostic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        return send_file(buffer, mimetype='text/plain', as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/account/delete', methods=['POST'])
@login_required
def delete_account():
    """Delete user account (GDPR compliance)."""
    email = current_user.email
    logout_user()
    user_store.delete_user_account(email)
    return redirect(url_for('login', deleted=1))


@app.route('/stripe/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events.
    For local testing: use `stripe listen --forward-to http://localhost:5001/stripe/webhook`.
    """
    payload = request.get_data(as_text=False)
    sig_header = request.headers.get('Stripe-Signature')

    # If Stripe not available or no webhook secret configured, accept silently
    if not STRIPE_AVAILABLE or not STRIPE_WEBHOOK_SECRET:
        return ('', 200)

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        return (f"Webhook signature verification failed: {str(e)}", 400)

    # Handle the checkout session completed event
    if event['type'] == 'checkout.session.completed':
        session_obj = event['data']['object']
        email = None
        if session_obj.get('customer_details'):
            email = (session_obj.get('customer_details') or {}).get('email')
        if not email:
            email = session_obj.get('customer_email')
        if email:
            try:
                user_store.mark_paid(email.lower())
            except Exception:
                pass

    return ('', 200)


@app.route('/pay')
def paywall():
    return (
        '<h2>Beta Access Required</h2>'
        '<p>This beta requires a one-time €9.99 payment.</p>'
        '<p><a href="/checkout">Buy access</a> to continue.</p>'
        '<p><a href="/login">Back to login</a></p>'
    )


@app.route('/health')
def health():
    """Health check endpoint for monitoring."""
    return {'status': 'healthy', 'service': 'finance-diagnostics'}, 200


@app.route('/admin/questionnaire-responses')
@login_required
@admin_required
def admin_questionnaire_responses():
    """Admin view for questionnaire responses (placeholder for future implementation)"""
    # In a real implementation, you would load responses from a database
    # For now, just show current session responses
    responses = session.get('questionnaire_responses', {})
    return render_template('admin_questionnaire.html', responses=responses)


@app.route('/admin/export-responses')
@login_required
@admin_required
def export_questionnaire_responses():
    """Export questionnaire responses to CSV"""
    from process_questionnaire_responses import export_responses_to_csv

    responses = session.get('questionnaire_responses', {})
    if not responses:
        return jsonify({'error': 'No responses to export'}), 400

    filename = export_responses_to_csv(responses)
    return send_file(filename, as_attachment=True, download_name=filename)


@app.route('/api/questionnaire', methods=['GET'])
def get_questionnaire():
    """API endpoint to get questionnaire data as JSON."""
    try:
        with open('questionnaire.json', 'r') as f:
            questionnaire_data = json.load(f)
        return jsonify(questionnaire_data)
    except FileNotFoundError:
        return jsonify({'error': 'Questionnaire not found'}), 404


@app.route('/api/questionnaire/responses', methods=['POST'])
@login_required
def submit_questionnaire_responses():
    """API endpoint to submit questionnaire responses."""
    try:
        responses = request.get_json()
        # Store responses in session or database
        session['questionnaire_responses'] = responses
        return jsonify({'success': True, 'message': 'Responses saved successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/questionnaire', methods=['GET', 'POST'])
@login_required
def questionnaire():
    """Dynamic questionnaire based on data gaps."""
    if request.method == 'POST':
        # Save questionnaire responses
        responses = request.form.to_dict()
        # Store in session or database
        from flask import session
        session['questionnaire_responses'] = responses
        return redirect(url_for('index'))
    
    # Load questionnaire from JSON file
    try:
        with open('questionnaire.json', 'r') as f:
            questionnaire_data = json.load(f)
        questionnaire = questionnaire_data['questionnaire']
        questions = questionnaire['questions']
    except FileNotFoundError:
        # Fallback to default questions if JSON file doesn't exist
        questionnaire = {
            'title': 'Complete Your Financial Profile',
            'description': 'Help us provide better insights by answering a few questions about areas we couldn\'t detect from your statements.'
        }
        questions = [
            {
                'id': 'insurance_coverage',
                'category': 'Insurance',
                'question': 'What types of insurance coverage do you currently have?',
                'type': 'multiple_choice',
                'options': ['Health', 'Life', 'Disability', 'Home/Renters', 'Auto', 'None'],
                'required': True
            },
            {
                'id': 'financial_goals',
                'category': 'Goals',
                'question': 'What are your top 3 financial goals for the next 5 years?',
                'type': 'text',
                'required': True
            },
            {
                'id': 'risk_tolerance',
                'category': 'Investments',
                'question': 'How comfortable are you with investment risk?',
                'type': 'single_choice',
                'options': ['Very Conservative', 'Conservative', 'Moderate', 'Aggressive', 'Very Aggressive'],
                'required': True
            }
        ]
    return render_template('questionnaire.html', questions=questions, questionnaire=questionnaire)


if __name__ == '__main__':
    app.run(debug=True, port=5001, use_reloader=False)
