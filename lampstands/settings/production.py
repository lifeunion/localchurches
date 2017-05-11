from __future__ import absolute_import, unicode_literals

from .base import *
import os

env = os.environ.copy()
SECRET_KEY = env['SECRET_KEY']
ALLOWED_HOSTS = ['*']
DEBUG = True

# Parse database configuration from $DATABASE_URL
import dj_database_url
DATABASES['default'] =  dj_database_url.config()
    
# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

#STATICFILES_STORAGE = 'whitenoise.django.GzipManifestStaticFilesStorage'

#AWS_STORAGE_BUCKET_NAME = "lcstatic"
#AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME
#MEDIAFILES_LOCATION="images"
#MEDIA_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, MEDIAFILES_LOCATION)
#DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_HOST_USER = env['SENDGRID_USERNAME']
EMAIL_HOST_PASSWORD = env['SENDGRID_PASSWORD']
EMAIL_PORT = 587
EMAIL_USE_TLS = True

COMPRESS_OFFLINE = True
COMPRESS_CSS_FILTERS = [
    'compressor.filters.css_default.CssAbsoluteFilter',
    'compressor.filters.cssmin.CSSMinFilter',
]
COMPRESS_CSS_HASHING_METHOD = 'content'

#set S3 as the place to store your files.
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
STATICFILES_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
AWS_ACCESS_KEY_ID = os.environ.get(“AWS_ACCESS_KEY_ID”, “”)
AWS_SECRET_ACCESS_KEY = os.environ.get(“AWS_SECRET_ACCESS_KEY”, “”)
AWS_STORAGE_BUCKET_NAME = os.environ.get(“AWS_STORAGE_BUCKET_NAME”, “”)
AWS_QUERYSTRING_AUTH = False //This will make sure that the file URL does not have unnecessary parameters like your access key.
AWS_S3_CUSTOM_DOMAIN = AWS_STORAGE_BUCKET_NAME + '.s3.amazonaws.com'
#static media settings
STATIC_URL = ‘https://' + AWS_STORAGE_BUCKET_NAME + '.s3.amazonaws.com/'
MEDIA_URL = STATIC_URL + 'media/'
STATICFILES_DIRS = ( os.path.join(BASE_DIR, "static"), )
STATIC_ROOT = 'static'
ADMIN_MEDIA_PREFIX = STATIC_URL + 'admin/'
STATICFILES_FINDERS = (
'django.contrib.staticfiles.finders.FileSystemFinder',
'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)


try:
    from .local import *
except ImportError:
    pass