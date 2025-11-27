import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash


DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'users.db')


def init_db():
    """Initialize the database and create users table if it doesn't exist."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reset_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            used INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    
    # Insert demo user if not exists
    try:
        cursor.execute('INSERT INTO users (email, password_hash) VALUES (?, ?)',
                      ('demo@example.com', generate_password_hash('Demo123!')))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # User already exists
    
    conn.close()


def get_user_by_email(email):
    """Retrieve user by email."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None


def verify_user(email, password):
    """Verify user credentials."""
    user = get_user_by_email(email)
    if user and check_password_hash(user['password_hash'], password):
        return user
    return None


def create_user(email, password):
    """Create a new user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO users (email, password_hash) VALUES (?, ?)',
                      (email, generate_password_hash(password)))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return get_user_by_email(email)
    except sqlite3.IntegrityError:
        conn.close()
        return None  # User already exists


def create_reset_token(email):
    """Create a password reset token for user."""
    import secrets
    from datetime import datetime, timedelta
    
    user = get_user_by_email(email)
    if not user:
        return None
    
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(hours=1)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO reset_tokens (user_id, token, expires_at) VALUES (?, ?, ?)',
                  (user['id'], token, expires_at))
    conn.commit()
    conn.close()
    return token


def verify_reset_token(token):
    """Verify and return user for valid reset token."""
    from datetime import datetime
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT rt.*, u.email FROM reset_tokens rt
        JOIN users u ON rt.user_id = u.id
        WHERE rt.token = ? AND rt.used = 0 AND rt.expires_at > ?
    ''', (token, datetime.now()))
    result = cursor.fetchone()
    conn.close()
    return dict(result) if result else None


def reset_password(token, new_password):
    """Reset password using valid token."""
    token_data = verify_reset_token(token)
    if not token_data:
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?',
                  (generate_password_hash(new_password), token_data['user_id']))
    cursor.execute('UPDATE reset_tokens SET used = 1 WHERE token = ?', (token,))
    conn.commit()
    conn.close()
    return True


def export_user_data(email):
    """Export all user data (GDPR compliance)."""
    user = get_user_by_email(email)
    if not user:
        return None
    
    return {
        'email': user['email'],
        'created_at': user['created_at'],
        'note': 'Financial transaction data is not stored on server; only uploaded temporarily for analysis.'
    }


def delete_user_account(email):
    """Delete user account and all associated data (GDPR compliance)."""
    user = get_user_by_email(email)
    if not user:
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM reset_tokens WHERE user_id = ?', (user['id'],))
    cursor.execute('DELETE FROM users WHERE id = ?', (user['id'],))
    conn.commit()
    conn.close()
    return True
