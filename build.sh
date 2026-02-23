#!/usr/bin/env bash
# exit on error
set -o errexit

# Use staging for non-master branches: static→WhiteNoise only, lcstatic S3 never touched.
if [ "${RENDER_GIT_BRANCH:-master}" = "master" ]; then
  export DJANGO_SETTINGS_MODULE=lampstands.settings.production
else
  export DJANGO_SETTINGS_MODULE=lampstands.settings.staging
fi
echo "DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE} (RENDER_GIT_BRANCH=${RENDER_GIT_BRANCH:-master})"

pip install -r requirements.txt

# Run database migrations
# First show migration status, then apply all migrations
echo "Checking migration status..."
python manage.py showmigrations --list || true

# Pre-migrate: fix revision content JSON so 0071_populate_revision_content_type doesn't FK-fail.
# 0071 sets content_type_id from content.content_type; if that ID is missing from django_content_type, migrate fails.
echo "Pre-migrate: fixing revision content JSON with invalid content_type..."
python manage.py fix_revision_content_json || true

# Run migrations with error handling
echo "Running migrations..."
python manage.py migrate --no-input --run-syncdb 2>&1 | tee /tmp/migrate.log || {
    MIGRATE_EXIT_CODE=$?
    # If migration fails due to foreign key constraint on revisions, fix it
    if grep -q "wagtailcore_revision.*foreign key constraint" /tmp/migrate.log; then
        echo "Fixing revision content_type_id and content JSON for foreign key issues..."
        python manage.py fix_revision_content_json || true
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

# Fix missing lampstands_orgpage intro/body columns (admin "Organizations listing" 500)
echo "Checking for missing lampstands_orgpage intro/body columns..."
python manage.py fix_orgpage || {
    echo "Warning: Could not fix orgpage columns, but continuing..."
}

# Ensure wagtailcore_referenceindex exists (Wagtail 6 page editor "Usage" panel)
# Must succeed or build fails (no silent deploy without the table).
echo "Checking for wagtailcore_referenceindex table..."
python manage.py fix_referenceindex

# Verify ChurchPage position restore was already applied (prevents removing restore block too early).
# If this fails: run "python manage.py restore_position_from_revisions" in Render Shell, then redeploy.
# Safe to remove this block once it has passed on a deploy.
echo "Verifying ChurchPage position restore..."
RESTORE_OUTPUT=$(python manage.py restore_position_from_revisions --dry-run 2>&1) || true
echo "$RESTORE_OUTPUT"
if echo "$RESTORE_OUTPUT" | grep -qE "Would restore position for [1-9][0-9]*"; then
    echo "ERROR: Position restore not yet applied. Run in Render Shell: python manage.py restore_position_from_revisions"
    exit 1
fi
echo "OK: No position restore needed."

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
# Use same settings as build (from RENDER_GIT_BRANCH in build.sh)
os.environ['DJANGO_SETTINGS_MODULE'] = os.environ.get('DJANGO_SETTINGS_MODULE') or 'lampstands.settings.production'
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

# Collect static (uses DJANGO_SETTINGS_MODULE set at top from RENDER_GIT_BRANCH).
echo "Running collectstatic with DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE}"
python manage.py collectstatic --no-input --clear --verbosity 2 2>&1 | tee /tmp/collectstatic.log || {
    echo "Warning: collectstatic had issues, checking log..."
    cat /tmp/collectstatic.log | tail -50
    echo ""
    echo "Trying collectstatic again without --clear..."
    python manage.py collectstatic --no-input --verbosity 2 || {
        echo "Error: collectstatic failed completely"
        cat /tmp/collectstatic.log | tail -100
        exit 1
    }
}

# Verify critical Wagtail admin files were collected
# When using S3: check object in bucket (collectstatic uploads there). When WhiteNoise: check STATIC_ROOT.
echo ""
echo "Verifying Wagtail admin CSS and JS files were collected..."
python -c "
import os
import sys
# Use same settings as build (from RENDER_GIT_BRANCH in build.sh)
os.environ['DJANGO_SETTINGS_MODULE'] = os.environ.get('DJANGO_SETTINGS_MODULE') or 'lampstands.settings.production'
import django
django.setup()
from django.conf import settings

# Use actual storage: staging/production without S3 use WhiteNoise (staticfiles); production with S3 uses s3boto3.
use_s3 = 's3boto3' in str(getattr(settings, 'STORAGES', {}).get('staticfiles', {}).get('BACKEND', ''))
checks = [
    ('wagtailadmin/css/core.css', 'Wagtail admin CSS'),
    ('wagtailadmin/js/common.js', 'Wagtail admin common.js (webpack runtime)'),
]
if not use_s3:
    checks += [
        ('css/villareal-turquoise.css', 'Site theme CSS'),
        ('css/font-awesome.min.css', 'Font Awesome'),
        ('js/villareal/jquery.min.js', 'jQuery'),
        ('js/villareal/tether.min.js', 'Tether'),
        ('js/villareal/bootstrap.min.js', 'Bootstrap'),
        ('css/libraries/owl-carousel/owl.carousel.min.js', 'Owl Carousel'),
        ('js/villareal/jquery.geocomplete.min.js', 'jQuery Geocomplete'),
        ('js/villareal/jquery1.7.1googapi.min.js', 'jQuery 1.7.1 Google API'),
        ('css/img/bluemap.jpg', 'Bluemap image'),
        ('css/img/vessel1.jpg', 'Vessel1 image'),
        ('lampstands/css/packages/src/markerclusterer.min.js', 'Map MarkerClusterer'),
        ('lampstands/css/packages/src/mapStoreLocator.js', 'Map mapStoreLocator'),
        ('lampstands/css/packages/src/style.css', 'Map style CSS'),
    ]

def check_s3(key):
    try:
        import boto3
        from botocore.exceptions import ClientError
        loc = getattr(settings, 'AWS_LOCATION', '') or ''
        k = (loc + '/' + key).lstrip('/') if loc else key
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1')
        )
        s3.head_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=k)
        return True, f's3://{settings.AWS_STORAGE_BUCKET_NAME}/{k}'
    except Exception as e:
        return False, str(e)

def check_local(key):
    path = os.path.join(settings.STATIC_ROOT, *key.split('/'))
    if os.path.exists(path):
        return True, f'{path} ({os.path.getsize(path)} bytes)'
    return False, f'not found at {path}'

ok = True
for key, label in checks:
    if use_s3:
        found, msg = check_s3(key)
    else:
        found, msg = check_local(key)
    if found:
        print(f'✅ {label}: {msg}')
    else:
        print(f'❌ {label} NOT found: {msg}')
        ok = False

if not ok:
    sys.exit(1)
" 2>&1

# Optional: warm CloudFront edge caches after collectstatic (only if CLOUDFRONT_STATIC_URL is set)
if [ -n "${CLOUDFRONT_STATIC_URL:-}" ] && [ -f ./scripts/warm_cloudfront.sh ]; then
    echo ""
    echo "Warming CloudFront caches..."
    bash ./scripts/warm_cloudfront.sh || echo "Warning: CloudFront warming failed, continuing."
fi
