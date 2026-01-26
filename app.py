"""
Shim for gunicorn/cloud hosts that expect `app:app` (e.g. Render Start Command override).
Delegates to Django WSGI. Prefer: gunicorn lampstands.wsgi:application
"""
from lampstands.wsgi import application

app = application
