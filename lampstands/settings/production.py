from __future__ import absolute_import, unicode_literals

from .base import *
import os

env = os.environ.copy()
SECRET_KEY = env.get('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required")

ALLOWED_HOSTS = ['*']
# Temporarily enable DEBUG to see error details - REMOVE AFTER FIXING
DEBUG = True

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
        'level': 'DEBUG',  # Changed to DEBUG to see all errors
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'DEBUG',  # Changed to DEBUG
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'DEBUG',  # Changed to DEBUG
            'propagate': False,
        },
        'wagtail': {
            'handlers': ['console'],
            'level': 'DEBUG',  # Changed to DEBUG
            'propagate': False,
        },
        'lampstands.core': {
            'handlers': ['console'],
            'level': 'DEBUG',  # Log all messages from our core module
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

# Static and media files configuration
# Use S3 if configured, otherwise use WhiteNoise for static files
if AWS_STORAGE_BUCKET_NAME and AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    # S3 storage for both static and media files
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    STATICFILES_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
    # Update STORAGES for S3
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        },
        "staticfiles": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        },
    }
else:
    # Use WhiteNoise for static files (no S3)
    # Using CompressedStaticFilesStorage instead of CompressedManifestStaticFilesStorage
    # to avoid issues with missing source map files
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
    STATIC_URL = '/static/'
    MEDIA_URL = '/media/'
    # Update STORAGES for WhiteNoise (inherited from base.py but ensure it's set)
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
        },
    }

STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"),)
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

# Wagtail admin base URL - use environment variable or default to Render URL
WAGTAILADMIN_BASE_URL = os.environ.get('WAGTAILADMIN_BASE_URL', 'https://localchurches.onrender.com')

try:
    from .local import *
except ImportError:
    pass
