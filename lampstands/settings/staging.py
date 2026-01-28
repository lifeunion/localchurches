"""
Staging settings: used for non-master branches (e.g. alpine-modernization).
- Static: WhiteNoise only (collectstatic → STATIC_ROOT). No S3.
- Media: FileSystemStorage (local). No S3.
- The lcstatic S3 bucket is never used; it is reserved for master/production only.
"""
from __future__ import absolute_import, unicode_literals

from .base import *
import os

env = os.environ.copy()
SECRET_KEY = env.get('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required")

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',') if os.environ.get('ALLOWED_HOSTS') else ['*']
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

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

import dj_database_url
import sys

database_url_raw = os.environ.get('DATABASE_URL', '')
if database_url_raw:
    import re
    database_url_masked = re.sub(r':([^:@]+)@', r':****@', database_url_raw)
    print(f"DEBUG: DATABASE_URL is set (masked): {database_url_masked[:80]}...", file=sys.stderr)
else:
    print("DEBUG: DATABASE_URL environment variable is NOT set!", file=sys.stderr)

db_config = dj_database_url.config(env='DATABASE_URL', default=None)
if db_config:
    DATABASES['default'] = db_config
    print(f"DEBUG: Database configured - Host: {db_config.get('HOST', 'N/A')}, Name: {db_config.get('NAME', 'N/A')}", file=sys.stderr)
else:
    print("ERROR: DATABASE_URL environment variable is not set!", file=sys.stderr)
    raise ValueError("DATABASE_URL environment variable is required. Link your database in Render dashboard.")

SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_HOST_USER = os.environ.get('SENDGRID_USERNAME', '')
EMAIL_HOST_PASSWORD = os.environ.get('SENDGRID_PASSWORD', '')
EMAIL_PORT = 587
EMAIL_USE_TLS = True
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

# ---- Staging: never use S3. lcstatic is reserved for master/production only. ----
# Static: WhiteNoise (collectstatic → STATIC_ROOT). Media: local filesystem.
# Use StaticFilesStorage (not CompressedStaticFilesStorage) to avoid post_process
# issues that can skip or fail on some files during collectstatic on Render, which
# led to 404s and "MIME type 'text/html'" when Django's 404 page was returned for
# missing CSS/JS. WhiteNoise still gzips responses on the fly.
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
STATIC_URL = '/static/'
MEDIA_URL = '/media/'
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),   # project root: css/, js/villareal/, etc.
    os.path.join(PROJECT_DIR, 'static'), # lampstands: lampstands/images/, etc.
)
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
print("DEBUG: Staging – using WhiteNoise for static (lcstatic S3 not used)", file=sys.stderr)
print(f"DEBUG: STATIC_ROOT = {STATIC_ROOT}", file=sys.stderr)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

WAGTAILADMIN_BASE_URL = os.environ.get('WAGTAILADMIN_BASE_URL', 'https://localchurches.onrender.com')

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'localchurches-cache-staging',
        'OPTIONS': {'MAX_ENTRIES': 1000},
    }
}

WHITENOISE_AUTOREFRESH = False
# Critical: if Render runtime starts without a populated STATIC_ROOT (e.g. collectstatic
# didn’t run or build artifacts weren’t persisted), this allows WhiteNoise to serve
# static assets directly from STATICFILES_DIRS via Django’s finders, preventing
# `/static/...` 404s (and the resulting “MIME type text/html” errors).
WHITENOISE_USE_FINDERS = True

try:
    from .local import *
except ImportError:
    pass
