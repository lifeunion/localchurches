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

# Migrate data from Heroku if HEROKU_DATABASE_URL is set and migration hasn't been done
if [ -n "$HEROKU_DATABASE_URL" ] && [ ! -f /tmp/.heroku_migration_complete ]; then
    echo "Heroku database URL detected. Running migration..."
    python migrate_from_heroku.py && touch /tmp/.heroku_migration_complete || echo "Migration failed or skipped"
fi

# Collect static files
python manage.py collectstatic --no-input
