#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Run database migrations
# First show migration status, then apply all migrations
echo "Checking migration status..."
python manage.py showmigrations --list || true

# Run syncdb first to ensure all models are created
echo "Running syncdb to create all models..."
python manage.py migrate --run-syncdb --no-input || true

echo "Running migrations..."
# Handle migration errors for problematic Wagtail migrations
python manage.py migrate --no-input 2>&1 | tee /tmp/migrate.log || {
    # If migration fails due to foreign key constraint on revisions, fix it
    if grep -q "wagtailcore_revision.*foreign key constraint" /tmp/migrate.log; then
        echo "Fixing revision content_type_id foreign key issues..."
        python -c "
import django
django.setup()
from django.db import connection
with connection.cursor() as cursor:
    # Set NULL for revisions with invalid content_type_id
    cursor.execute('''
        UPDATE wagtailcore_revision 
        SET content_type_id = NULL 
        WHERE content_type_id IS NOT NULL 
        AND content_type_id NOT IN (SELECT id FROM django_content_type)
    ''')
    print(f'Fixed {cursor.rowcount} revision records')
"
        # Retry migration
        echo "Retrying migrations after fixing revisions..."
        python manage.py migrate --no-input
    else
        echo "Migration failed with unknown error"
        cat /tmp/migrate.log
        exit 1
    fi
}

# Migrate data from Heroku if HEROKU_DATABASE_URL is set and migration hasn't been done
if [ -n "$HEROKU_DATABASE_URL" ] && [ ! -f /tmp/.heroku_migration_complete ]; then
    echo "Heroku database URL detected. Running migration..."
    python migrate_from_heroku.py && touch /tmp/.heroku_migration_complete || echo "Migration failed or skipped"
fi

# Collect static files
python manage.py collectstatic --no-input
