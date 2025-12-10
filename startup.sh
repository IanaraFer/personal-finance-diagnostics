#!/bin/bash
set -e

echo "Installing dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "Collecting static files..."
mkdir -p static

echo "Setting environment variables..."
export FLASK_ENV=production
export FLASK_DEBUG=False

echo "Deployment script completed successfully!"
