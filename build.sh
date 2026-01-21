#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Run database migrations
# First show migration status, then apply all migrations
echo "Checking migration status..."
python manage.py showmigrations --list || true
echo "Running migrations..."
python manage.py migrate --no-input --run-syncdb

# Collect static files
python manage.py collectstatic --no-input
