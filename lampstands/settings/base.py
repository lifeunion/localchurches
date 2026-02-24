"""
Django settings for lampstands project.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(PROJECT_DIR)
CORE_DIR = os.path.join(BASE_DIR, 'core')


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/


# Application definition

INSTALLED_APPS = [
    'lampstands.core',
    'search',
    'storages',
    'rest_framework',
    'crispy_forms',
    'crispy_bootstrap4',
    'wagtailcaptcha',
    'django_recaptcha',
    'wagtail.api.v2',

    # Wagtail contrib apps
    'wagtail.contrib.search_promotions',
    'wagtail.contrib.forms',
    'wagtail.contrib.redirects',
    'wagtail.contrib.settings',

    # Wagtail core apps
    'wagtail.embeds',
    'wagtail.sites',
    'wagtail.users',
    'wagtail.snippets',
    'wagtail.documents',
    'wagtail.images',
    'wagtail.search',
    'wagtail.admin',
    'wagtail',

    # wagtail-modeladmin (external package for Wagtail 6.x)
    'wagtail_modeladmin',

    # Map widget for address search + verify (ChurchPage, etc.)
    'wagtailgeowidget',

    'modelcluster',
    'taggit',

    # added from tbx settings
    'compressor',
    'django.contrib.humanize',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_countries',
]

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'wagtail.contrib.redirects.middleware.RedirectMiddleware',
    'lampstands.core.middleware.BlockOrganizationDetailMiddleware',
    'lampstands.core.middleware.CacheControlHeadersMiddleware',
]

# Block GET requests to organization detail URLs (e.g. /organizations-listing/dcp/)
# so they stay published but are not reachable by bots or URL traversal. Set to False to disable.
BLOCK_ORGANIZATION_DETAIL_URLS = True

ROOT_URLCONF = 'lampstands.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(CORE_DIR, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Temporarily disabled to debug 500 errors
                # 'wagtail.contrib.settings.context_processors.settings',
            ],
        },
    },
]


WSGI_APPLICATION = 'lampstands.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'd85jsi3phqta5n',
        'HOST': 'ec2-54-243-124-240.compute-1.amazonaws.com',
        'PASSWORD': '1edeae694aa4e49354562c4b36fefdc6eded2fc251f9615558b4ce013aa4ba0b',
        'USER': 'iqmxhqvsegcfet',
    }
}

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # added through tbx
    'compressor.finders.CompressorFinder',
]

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),   # project root: css/, js/villareal/, etc.
    os.path.join(PROJECT_DIR, 'static'), # lampstands: lampstands/images/, etc.
]

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        # Keep base settings aligned with staging’s “no post_process surprises” approach.
        # staging.py/production.py override this as needed, but base should be safe.
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

AWS_STORAGE_BUCKET_NAME = 'lcstatic'
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME

# added through tbx
# Django compressor settings
# http://django-compressor.readthedocs.org/en/latest/settings/

COMPRESS_PRECOMPILERS = [
    ('text/x-scss', 'django_libsass.SassCompiler'),
]

# Wagtail settings
WAGTAIL_SITE_NAME = "lampstands"

# Base URL to use when referring to full URLs within the Wagtail admin backend -
# e.g. in notification emails. Don't include '/admin' or a trailing slash
# Use environment variable if set, otherwise default to localhost for development
WAGTAILADMIN_BASE_URL = os.environ.get('WAGTAILADMIN_BASE_URL', 'http://localhost:8000')

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Override the Image class used by wagtailimages with a custom one
WAGTAILIMAGES_IMAGE_MODEL = 'lampstands.LampstandsImage'

GEOPOSITION_GOOGLE_MAPS_API_KEY = 'AIzaSyA4MAVqADcBv3nSIqd8y7RZWF9kmcVB6XQ'

# wagtail-geo-widget: address search + map verify in admin (Geocoding + Maps JavaScript API)
GOOGLE_MAPS_V3_APIKEY = os.environ.get('GOOGLE_MAPS_V3_APIKEY', GEOPOSITION_GOOGLE_MAPS_API_KEY)

# Map ID for Advanced Markers (removes google.maps.Marker deprecation).
# DEMO_MAP_ID works for testing; for production create one in Google Cloud
# Console → Google Maps Platform → Map Management. Set to '' to fall back to
# classic (deprecated) Marker.
GOOGLE_MAPS_MAP_ID = os.environ.get('GOOGLE_MAPS_MAP_ID', 'DEMO_MAP_ID')

# Wagtail uses Draftail as the default rich text editor (no configuration needed)

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
        'rest_framework_csv.renderers.CSVRenderer',
    )
}

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap4"
CRISPY_TEMPLATE_PACK = 'bootstrap4'
