import os
from flask import Flask
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Application factory for Azure deployment"""
    from app import app as flask_app
    
    # Azure-specific configuration
    flask_app.config['ENV'] = os.environ.get('FLASK_ENV', 'production')
    flask_app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Security headers
    @flask_app.after_request
    def set_security_headers(response):
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response
    
    logger.info(f"Application initialized in {flask_app.config['ENV']} mode")
    return flask_app

app = create_app()

if __name__ == "__main__":
    # For local development - Azure uses gunicorn
    app.run()
