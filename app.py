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
    # Load sample data for the landing demo
    tx_df, acct_df = load_sample_data()
    results = analyze_finances(tx_df, acct_df)
    return render_template('dashboard_enhanced.html', results=results)


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        tx_file = request.files.get('transactions')
        acct_file = request.files.get('accounts')
        if not tx_file:
            return render_template('upload.html', error='Please provide a transactions file.')

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
                    tx_df['amount'] = pd.to_numeric(tx_df['credit'], errors='coerce').fillna(0) - pd.to_numeric(tx_df['debit'], errors='coerce').fillna(0)
                elif {'money_in', 'money_out'}.issubset(cols):
                    tx_df['amount'] = pd.to_numeric(tx_df['money_in'], errors='coerce').fillna(0) - pd.to_numeric(tx_df['money_out'], errors='coerce').fillna(0)
                elif {'deposit', 'withdrawal'}.issubset(cols):
                    tx_df['amount'] = pd.to_numeric(tx_df['deposit'], errors='coerce').fillna(0) - pd.to_numeric(tx_df['withdrawal'], errors='coerce').fillna(0)
                elif 'value' in cols:
                    tx_df['amount'] = pd.to_numeric(tx_df['value'], errors='coerce')
                elif 'transaction_amount' in cols:
                    tx_df['amount'] = pd.to_numeric(tx_df['transaction_amount'], errors='coerce')
            # type
            if 'type' not in tx_df.columns:
                if 'dc' in tx_df.columns:  # debit/credit marker (e.g., 'D'/'C')
                    tx_df['type'] = tx_df['dc'].astype(str).str.upper().map({'C': 'income', 'CR': 'income', 'D': 'expense', 'DR': 'expense'})
                elif 'dr_cr' in tx_df.columns:
                    tx_df['type'] = tx_df['dr_cr'].astype(str).str.upper().map({'CR': 'income', 'DR': 'expense'})
                elif 'amount' in tx_df.columns:
                    tx_df['type'] = pd.to_numeric(tx_df['amount'], errors='coerce').fillna(0).apply(lambda x: 'income' if x > 0 else 'expense')
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
                    error=f'Could not detect required columns: {", ".join(missing)}. Detected columns: {detected}. If your bank uses different names, share the header row and I will map them.')

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
            return render_template('dashboard_enhanced.html', results=results)

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
            user = User(id=user_data['email'], email=user_data['email'], is_admin=user_data.get('is_admin', 0))
            login_user(user)
            # Redirect to dashboard instead of index (which is now the landing page)
            if getattr(user, 'is_admin', False):
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('paywall') if not user_store.has_paid(email) else url_for('index'))
        return render_template('login.html', error='Invalid credentials.')
    return render_template('login.html')


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
            'diagnostic_report': results.get('diagnostic_report', {})
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
    """Export financial health report as PDF."""
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
        diagnostic = results.get('diagnostic_report', {})
        
        # Create simple text-based report (PDF libraries like reportlab can be added later)
        report_lines = [
            "FINANCIAL HEALTH DIAGNOSTIC REPORT",
            "=" * 80,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"User: {current_user.email}",
            "",
            f"OVERALL HEALTH SCORE: {diagnostic.get('overall_score', 0):.0f}/100 (Grade: {diagnostic.get('grade', 'N/A')})",
            "",
            "CATEGORY SCORES:",
            "-" * 80
        ]
        
        for category, data in diagnostic.get('categories', {}).items():
            score = data.get('score', 0)
            status = data.get('status', 'unknown')
            report_lines.append(f"{category.replace('_', ' ').title():30s}: {score:3.0f}/100 ({status})")
        
        report_lines.extend([
            "",
            "FINANCIAL SUMMARY:",
            "-" * 80,
            f"Total Income:     €{results['income']:,.2f}",
            f"Total Expenses:   €{results['expenses']:,.2f}",
            f"Savings Rate:     {results['savings_rate']:.1f}%",
            ""
        ])
        
        # Add risks
        risks = diagnostic.get('risks', [])
        if risks:
            report_lines.extend(["RISKS IDENTIFIED:", "-" * 80])
            for i, risk in enumerate(risks, 1):
                report_lines.append(f"{i}. [{risk.get('severity', 'medium').upper()}] {risk.get('message', '')}")
            report_lines.append("")
        
        # Add recommendations
        recommendations = diagnostic.get('recommendations', [])
        if recommendations:
            report_lines.extend(["RECOMMENDATIONS:", "-" * 80])
            for i, rec in enumerate(recommendations, 1):
                report_lines.append(f"{i}. [{rec.get('priority', 'medium').upper()}] {rec.get('action', '')}")
                report_lines.append(f"   Impact: {rec.get('impact', '')}")
                report_lines.append("")
        
        # Create text file (can be enhanced to proper PDF later)
        report_text = "\n".join(report_lines)
        buffer = io.BytesIO()
        buffer.write(report_text.encode('utf-8'))
        buffer.seek(0)
        
        # Generate filename with timestamp
        filename = f"financial_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        return send_file(
            buffer,
            mimetype='text/plain',
            as_attachment=True,
            download_name=filename
        )
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


@app.route('/demo')
def demo():
    """Demo route - interactive file upload for analysis, no authentication required."""
    return render_template('demo.html')


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
    
    # Get questionnaire from latest analysis
    # For demo purposes, render empty questionnaire template
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
    return render_template('questionnaire.html', questions=questions)


if __name__ == '__main__':
    app.run(debug=True, port=5001, use_reloader=False)
