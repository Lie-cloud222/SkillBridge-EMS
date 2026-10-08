import os
from .base import *

DEBUG = False

# Fall back safely during build if DJANGO_SECRET_KEY isn't set
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'build-only-secret-key')

# Check if running inside the Docker build step
IS_BUILDING = SECRET_KEY == "build-only"

ALLOWED_HOSTS = [h for h in os.environ.get('ALLOWED_HOSTS', '').split(',') if h]
RENDER_HOST = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_HOST:
    ALLOWED_HOSTS.append(RENDER_HOST)
    CSRF_TRUSTED_ORIGINS = [f'https://{RENDER_HOST}']

# Render terminates HTTPS at its proxy
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

if IS_BUILDING:
    # Use SQLite in-memory database to prevent db connection attempts during Docker build
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }
    # Use standard static storage during build to prevent missing manifest file crashes
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
else:
    # Production WhiteNoise storage for serving assets efficiently
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    }
    
    # Safely configure Azure SQL extra parameters if DATABASES is defined in base.py
    if 'DATABASES' in locals() and 'default' in DATABASES:
        DATABASES['default'].setdefault('OPTIONS', {})['extra_params'] = 'Encrypt=yes;TrustServerCertificate=no;'

MAILERS = {
    "default": {"BACKEND": "django.core.mail.backends.smtp.EmailBackend"},
}