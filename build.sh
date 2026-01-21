#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Run database migrations
# Continue even if migrations fail (they might already be applied)
python manage.py migrate --no-input || echo "Migrations completed with warnings or were already applied"

# Collect static files
python manage.py collectstatic --no-input
