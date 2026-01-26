from __future__ import absolute_import, unicode_literals

from .base import *
import os

env = os.environ.copy()
SECRET_KEY = env.get('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required")

# Security: Set ALLOWED_HOSTS from environment variable or use wildcard as fallback
# In production, set ALLOWED_HOSTS env var to your domain(s), e.g., "yourdomain.com,www.yourdomain.com"
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',') if os.environ.get('ALLOWED_HOSTS') else ['*']

# Security: DEBUG should be False in production
# Set DEBUG=True in environment variable only for temporary debugging
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# Enable detailed error logging to console for debugging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        # Use INFO in production, DEBUG only when troubleshooting
        'level': os.environ.get('LOG_LEVEL', 'INFO'),
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.environ.get('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': os.environ.get('DJANGO_REQUEST_LOG_LEVEL', 'WARNING'),
            'propagate': False,
        },
        'wagtail': {
            'handlers': ['console'],
            'level': os.environ.get('WAGTAIL_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'lampstands.core': {
            'handlers': ['console'],
            'level': os.environ.get('LAMPSTANDS_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
    },
}

# Parse database configuration from $DATABASE_URL
# In production, DATABASE_URL must be set (automatically set when database is linked in Render)
import dj_database_url
import sys

# Debug: Log what DATABASE_URL is set to (masking password)
database_url_raw = os.environ.get('DATABASE_URL', '')
if database_url_raw:
    # Mask password in URL for logging
    import re
    database_url_masked = re.sub(r':([^:@]+)@', r':****@', database_url_raw)
    print(f"DEBUG: DATABASE_URL is set (masked): {database_url_masked[:80]}...", file=sys.stderr)
else:
    print("DEBUG: DATABASE_URL environment variable is NOT set!", file=sys.stderr)

# Explicitly read from DATABASE_URL env var
db_config = dj_database_url.config(env='DATABASE_URL', default=None)
if db_config:
    DATABASES['default'] = db_config
    print(f"DEBUG: Database configured - Host: {db_config.get('HOST', 'N/A')}, Name: {db_config.get('NAME', 'N/A')}", file=sys.stderr)
else:
    # DATABASE_URL is required in production
    print("ERROR: DATABASE_URL environment variable is not set!", file=sys.stderr)
    print("Please link your Render Postgres database to this service in the Render dashboard.", file=sys.stderr)
    print("This will automatically set the DATABASE_URL environment variable.", file=sys.stderr)
    raise ValueError("DATABASE_URL environment variable is required in production. Link your database in Render dashboard.")

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Email settings - use env vars with fallback to console backend
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_HOST_USER = os.environ.get('SENDGRID_USERNAME', '')
EMAIL_HOST_PASSWORD = os.environ.get('SENDGRID_PASSWORD', '')
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# Fall back to console email if SendGrid not configured
if not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

COMPRESS_OFFLINE = True
COMPRESS_CSS_FILTERS = [
    'compressor.filters.css_default.CssAbsoluteFilter',
    'compressor.filters.cssmin.CSSMinFilter',
]
COMPRESS_CSS_HASHING_METHOD = 'content'
# Admin CSS safeguard: Wagtail admin does NOT use {% compress %} for core.css; it uses
# {% versioned_static 'wagtailadmin/css/core.css' %}. Compressor only processes {% compress %}
# blocks, so wagtailadmin assets are already excluded. Do not wrap admin base or skeleton
# in {% compress %}; that would break admin CSS.

RECAPTCHA_PUBLIC_KEY = os.environ.get("GOOGLE_RECAPTCHA_SITE_KEY", "")
RECAPTCHA_PRIVATE_KEY = os.environ.get("GOOGLE_RECAPTCHA_SECRET_KEY", "")
NOCAPTCHA = True
RECAPTCHA_USE_SSL = True

# AWS S3 Settings
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
AWS_STORAGE_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "")
AWS_QUERYSTRING_AUTH = False
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com' if AWS_STORAGE_BUCKET_NAME else None

# Debug S3 configuration
import sys
has_bucket = bool(AWS_STORAGE_BUCKET_NAME)
has_access_key = bool(AWS_ACCESS_KEY_ID)
has_secret_key = bool(AWS_SECRET_ACCESS_KEY)
print(f"DEBUG S3 Config: bucket={has_bucket}, access_key={has_access_key}, secret_key={has_secret_key}", file=sys.stderr)
if has_bucket:
    print(f"DEBUG S3 Bucket Name: {AWS_STORAGE_BUCKET_NAME}", file=sys.stderr)
if has_access_key:
    print(f"DEBUG S3 Access Key: {AWS_ACCESS_KEY_ID[:8]}...", file=sys.stderr)

# Static and media files configuration
# Use S3 if configured, otherwise use WhiteNoise for static files
if AWS_STORAGE_BUCKET_NAME and AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    # S3 storage for both static and media files
    print(f"DEBUG: Configuring S3 storage backend", file=sys.stderr)
    print(f"DEBUG: STATIC_URL will be: https://{AWS_S3_CUSTOM_DOMAIN}/", file=sys.stderr)
    
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    STATICFILES_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
    
    # Additional S3 settings for better compatibility
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    AWS_DEFAULT_ACL = 'public-read'
    AWS_S3_REGION_NAME = 'us-east-1'  # Adjust if your bucket is in a different region
    AWS_S3_USE_SSL = True
    AWS_S3_VERIFY = True
    
    # IMPORTANT: Set location for static files in S3
    # This ensures static files are stored in the root of the bucket, not in a subdirectory
    # Without this, Wagtail admin CSS/JS files may not be found correctly
    AWS_LOCATION = ''  # Empty string means root of bucket
    
    # Ensure static files are collected with correct paths
    # This is critical for Wagtail admin files to load correctly
    AWS_S3_FILE_OVERWRITE = True  # Overwrite existing files so wagtailadmin and other statics update on each collectstatic
    AWS_IS_GZIPPED = False  # Let WhiteNoise handle compression if needed
    
    # Update STORAGES for S3
    # Note: Using plain S3Boto3Storage (not ManifestStaticFilesStorage) because:
    # - ManifestStaticFilesStorage requires manifest.json which may not work well with S3
    # - Wagtail 6.4 handles file versioning via query strings (?v=hash)
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        },
        "staticfiles": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        },
    }
    
    # Test S3 connection during startup (non-blocking)
    try:
        import boto3
        from botocore.exceptions import ClientError, NoCredentialsError
        s3_client = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_S3_REGION_NAME
        )
        # Try to list bucket (head_bucket is more lightweight)
        try:
            s3_client.head_bucket(Bucket=AWS_STORAGE_BUCKET_NAME)
            print(f"DEBUG: ✅ S3 connection successful - bucket '{AWS_STORAGE_BUCKET_NAME}' is accessible", file=sys.stderr)
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            print(f"DEBUG: ⚠️  S3 connection issue - Error: {error_code}", file=sys.stderr)
            print(f"DEBUG: S3 Error details: {str(e)[:200]}", file=sys.stderr)
        except NoCredentialsError:
            print(f"DEBUG: ❌ S3 credentials invalid or missing", file=sys.stderr)
        except Exception as e:
            print(f"DEBUG: ⚠️  S3 connection test failed: {type(e).__name__}: {str(e)[:200]}", file=sys.stderr)
    except ImportError:
        print(f"DEBUG: ⚠️  boto3 not available - cannot test S3 connection", file=sys.stderr)
    except Exception as e:
        print(f"DEBUG: ⚠️  Could not test S3 connection: {type(e).__name__}: {str(e)[:200]}", file=sys.stderr)
    
    # IMPORTANT: Remove WhiteNoise middleware when using S3
    # WhiteNoise only serves /static/ URLs, which conflicts with S3 URLs
    # WhiteNoise will intercept /static/ requests and return 404 for S3-hosted files
    if 'whitenoise.middleware.WhiteNoiseMiddleware' in MIDDLEWARE:
        MIDDLEWARE = [m for m in MIDDLEWARE if m != 'whitenoise.middleware.WhiteNoiseMiddleware']
        print(f"DEBUG: ✅ Removed WhiteNoise middleware (using S3 for static files)", file=sys.stderr)
    else:
        print(f"DEBUG: WhiteNoise middleware not found in MIDDLEWARE (expected when using S3)", file=sys.stderr)
else:
    # Use WhiteNoise for static files (no S3)
    # Use StaticFilesStorage (not CompressedStaticFilesStorage) to avoid post_process
    # skipping/failing files during collectstatic, which causes 404s and MIME type
    # errors when Django's HTML 404 page is returned for missing CSS/JS.
    # WhiteNoise still gzips responses on the fly.
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
    STATIC_URL = '/static/'
    MEDIA_URL = '/media/'
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
    # IMPORTANT: When using WhiteNoise, STATIC_ROOT (set below) must exist; start.sh
    # runs collectstatic so staticfiles/ is created when build output is not persisted.
    import sys
    print(f"DEBUG: Using WhiteNoise for static files", file=sys.stderr)
    print(f"DEBUG: STATIC_URL = {STATIC_URL}", file=sys.stderr)

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),   # project root: css/, js/villareal/, etc.
    os.path.join(PROJECT_DIR, 'static'), # lampstands: lampstands/images/, etc.
)
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# CompressorFinder is for {% compress %} blocks (site CSS/JS) only. Wagtail admin is
# not in any {% compress %} block and must remain that way.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

# Wagtail admin base URL - use environment variable or default to Render URL
WAGTAILADMIN_BASE_URL = os.environ.get('WAGTAILADMIN_BASE_URL', 'https://localchurches.onrender.com')

# Cache configuration for API response caching
# Using in-memory cache (fine for single server, upgrade to Redis if scaling to multiple servers)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'localchurches-cache',
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    }
}

# WhiteNoise configuration
# WhiteNoise 6.x automatically compresses responses (including API JSON) with gzip
# when client supports it (Accept-Encoding: gzip header) and content is compressible.
# CompressedStaticFilesStorage handles static file compression during collectstatic.
# No additional configuration needed - gzip compression is enabled by default.
WHITENOISE_AUTOREFRESH = False  # Disable auto-refresh in production for better performance

try:
    from .local import *
except ImportError:
    pass
