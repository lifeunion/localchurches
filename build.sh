#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Run database migrations
# First show migration status, then apply all migrations
echo "Checking migration status..."
python manage.py showmigrations --list || true

# Run migrations with error handling
echo "Running migrations..."
python manage.py migrate --no-input --run-syncdb 2>&1 | tee /tmp/migrate.log || {
    MIGRATE_EXIT_CODE=$?
    # If migration fails due to foreign key constraint on revisions, fix it
    if grep -q "wagtailcore_revision.*foreign key constraint" /tmp/migrate.log; then
        echo "Fixing revision content_type_id foreign key issues..."
        python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lampstands.settings.production')
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
        python manage.py migrate --no-input --run-syncdb || {
            echo "Migration still failed after fix attempt"
            cat /tmp/migrate.log
            exit 1
        }
    else
        echo "Migration failed with exit code: $MIGRATE_EXIT_CODE"
        echo "Migration log:"
        cat /tmp/migrate.log
        exit 1
    fi
}

# Verify migrations completed successfully
echo "Verifying migrations completed..."
python manage.py showmigrations --list | grep -E "\[ \]" && {
    echo "WARNING: Some migrations appear unapplied!"
    python manage.py migrate --no-input
} || echo "All migrations appear to be applied"

# Migrate data from Heroku if HEROKU_DATABASE_URL is set
# Use direct table copy which handles Wagtail tables in proper dependency order
if [ -n "$HEROKU_DATABASE_URL" ]; then
    echo "=========================================="
    echo "Heroku database URL detected."
    echo "Testing connection first..."
    echo "=========================================="
    if python test_heroku_connection.py 2>&1; then
        echo ""
        echo "=========================================="
        echo "Connection test passed. Running migration..."
        echo "=========================================="
        if python migrate_from_heroku.py 2>&1; then
            echo "✓ Migration completed successfully"
        else
            MIGRATION_EXIT_CODE=$?
            echo "✗ Migration failed with exit code: $MIGRATION_EXIT_CODE"
            echo "Check the output above for errors."
            echo "The deployment will continue, but data may not be migrated."
        fi
    else
        CONNECTION_EXIT_CODE=$?
        echo "✗ Connection test failed with exit code: $CONNECTION_EXIT_CODE"
        echo "Cannot proceed with migration. Check HEROKU_DATABASE_URL."
        echo "The deployment will continue, but migration will be skipped."
    fi
    echo "=========================================="
fi

# Fix Wagtail site configuration after migration
echo "=========================================="
echo "Fixing Wagtail site configuration..."
echo "=========================================="
python fix_wagtail_site.py 2>&1 || echo "Site configuration fix failed or skipped"
echo "=========================================="

# Run diagnostic check to see what was actually migrated
echo "=========================================="
echo "Running migration diagnostic check..."
echo "=========================================="
python check_migration_status.py 2>&1 || echo "Diagnostic check failed or skipped"
echo "=========================================="

# Collect static files
python manage.py collectstatic --no-input
