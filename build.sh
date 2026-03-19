#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "Updating pip and installing requirements..."
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Checking database tables or running migrations..."
python manage.py migrate --no-input
