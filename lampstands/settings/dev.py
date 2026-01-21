from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
SECRET_KEY = '4tp-x_*%a=nrobcg%ykb48p%b%9^$00=&q82!-i5&v8lfi=*h5'

ALLOWED_HOSTS = ['*']

try:
    from .local import *
except ImportError:
    pass
