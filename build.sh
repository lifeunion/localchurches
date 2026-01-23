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

# Fix missing Wagtail userprofile columns (common after Heroku migration)
echo "Checking for missing Wagtail userprofile columns..."
python manage.py fix_userprofile || {
    echo "Warning: Could not fix userprofile columns, but continuing..."
}

# Fix missing Wagtail workflowstate columns (common after Heroku migration)
echo "Checking for missing Wagtail workflowstate columns..."
python manage.py fix_workflowstate || {
    echo "Warning: Could not fix workflowstate columns, but continuing..."
}

# Fix missing Wagtail taskstate columns (common after Heroku migration)
echo "Checking for missing Wagtail taskstate columns..."
python manage.py fix_taskstate || {
    echo "Warning: Could not fix taskstate columns, but continuing..."
}

# Fix missing Wagtail revision columns (common after Heroku migration)
echo "Checking for missing Wagtail revision columns..."
python manage.py fix_revision || {
    echo "Warning: Could not fix revision columns, but continuing..."
}

# Fix missing Wagtail document columns (common after Heroku migration)
echo "Checking for missing Wagtail document columns..."
python manage.py fix_document || {
    echo "Warning: Could not fix document columns, but continuing..."
}

# Fix missing LampstandsImage columns (common after Heroku migration)
echo "Checking for missing LampstandsImage columns..."
python manage.py fix_lampstandsimage || {
    echo "Warning: Could not fix lampstandsimage columns, but continuing..."
}

# Verify migrations completed successfully
echo "Verifying migrations completed..."
python manage.py showmigrations --list | grep -E "\[ \]" && {
    echo "WARNING: Some migrations appear unapplied!"
    python manage.py migrate --no-input
} || echo "All migrations appear to be applied"

# Collect static files
# Use --clear to ensure all files are collected, including webpack chunks
# Use --verbosity 2 to see which files are being collected (helps debug)
echo "Collecting static files..."
echo "Checking static file storage backend..."
python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lampstands.settings.production')
import django
django.setup()
from django.conf import settings
print(f'STATICFILES_STORAGE: {settings.STATICFILES_STORAGE}')
print(f'STATIC_URL: {settings.STATIC_URL}')
print(f'STATIC_ROOT: {settings.STATIC_ROOT}')

# Check S3 configuration
has_bucket = bool(getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None))
has_access_key = bool(getattr(settings, 'AWS_ACCESS_KEY_ID', None))
has_secret_key = bool(getattr(settings, 'AWS_SECRET_ACCESS_KEY', None))
has_s3 = has_bucket and has_access_key and has_secret_key

print(f'')
print(f'S3 Configuration Check:')
print(f'  Bucket name set: {has_bucket}')
if has_bucket:
    print(f'  Bucket: {settings.AWS_STORAGE_BUCKET_NAME}')
print(f'  Access key set: {has_access_key}')
print(f'  Secret key set: {has_secret_key}')
print(f'  Using S3: {has_s3}')

if has_s3:
    print(f'')
    print(f'✅ S3 is configured - files will be uploaded to S3')
    print(f'   STATIC_URL: {settings.STATIC_URL}')
    print(f'   Expected URL format: {settings.STATIC_URL}wagtailadmin/css/core.css')
    
    # Test S3 connection
    try:
        import boto3
        from botocore.exceptions import ClientError, NoCredentialsError
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1')
        )
        try:
            s3_client.head_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
            print(f'   ✅ S3 bucket is accessible')
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            print(f'   ❌ S3 bucket access failed: {error_code}')
            print(f'      Error: {str(e)[:150]}')
        except Exception as e:
            print(f'   ⚠️  S3 connection test error: {type(e).__name__}: {str(e)[:150]}')
    except ImportError:
        print(f'   ⚠️  boto3 not available - cannot test S3 connection')
    except Exception as e:
        print(f'   ⚠️  Could not test S3: {type(e).__name__}: {str(e)[:150]}')
else:
    print(f'')
    print(f'⚠️  WARNING: No S3 credentials - using WhiteNoise')
    print(f'   Files will be collected to: {settings.STATIC_ROOT}')
    print(f'   STATIC_URL: {settings.STATIC_URL}')
" || echo "Could not check storage backend"

# Temporarily disable S3 storage during collectstatic if credentials are missing
# This ensures files are collected locally for WhiteNoise
python manage.py collectstatic --no-input --clear --verbosity 2 2>&1 | tee /tmp/collectstatic.log || {
    echo "Warning: collectstatic had issues, checking log..."
    cat /tmp/collectstatic.log | tail -50
    echo ""
    echo "Trying collectstatic again without --clear..."
    # Try again without --clear as fallback
    python manage.py collectstatic --no-input --verbosity 2 || {
        echo "Error: collectstatic failed completely"
        cat /tmp/collectstatic.log | tail -100
        exit 1
    }
}

# Verify critical Wagtail admin files were collected
echo ""
echo "Verifying Wagtail admin CSS files were collected..."
python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lampstands.settings.production')
import django
django.setup()
from django.conf import settings
css_path = os.path.join(settings.STATIC_ROOT, 'wagtailadmin', 'css', 'core.css')
if os.path.exists(css_path):
    print(f'✅ Wagtail admin CSS found: {css_path}')
    print(f'   File size: {os.path.getsize(css_path)} bytes')
else:
    print(f'❌ Wagtail admin CSS NOT found: {css_path}')
    print(f'   STATIC_ROOT: {settings.STATIC_ROOT}')
    print(f'   STATIC_ROOT exists: {os.path.exists(settings.STATIC_ROOT)}')
    # List what's actually in STATIC_ROOT
    if os.path.exists(settings.STATIC_ROOT):
        import subprocess
        try:
            result = subprocess.run(['find', settings.STATIC_ROOT, '-name', 'core.css', '-type', 'f'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout:
                print(f'   Found core.css files:')
                for line in result.stdout.strip().split('\n')[:5]:
                    print(f'     {line}')
            else:
                print(f'   No core.css files found in STATIC_ROOT')
                # List top-level directories
                try:
                    dirs = [d for d in os.listdir(settings.STATIC_ROOT) if os.path.isdir(os.path.join(settings.STATIC_ROOT, d))][:10]
                    print(f'   Top-level directories in STATIC_ROOT: {dirs}')
                except:
                    pass
        except Exception as e:
            print(f'   Error checking files: {e}')
" 2>&1 || echo "⚠️  Could not verify Wagtail admin CSS files"
