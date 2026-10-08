import os

from .base import *

DEBUG = False
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']          # set on the host, never in Git

ALLOWED_HOSTS = [h for h in os.environ.get('ALLOWED_HOSTS', '').split(',') if h]
RENDER_HOST = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_HOST:
    ALLOWED_HOSTS.append(RENDER_HOST)
    CSRF_TRUSTED_ORIGINS = [f'https://{RENDER_HOST}']

# Render terminates HTTPS at its proxy, so Django must trust the forwarded header,
# or SECURE_SSL_REDIRECT causes an endless redirect loop.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# Azure SQL needs encryption and a verified certificate
DATABASES['default']['OPTIONS']['extra_params'] = 'Encrypt=yes;TrustServerCertificate=no;'

MAILERS = {
    "default": {"BACKEND": "django.core.mail.backends.smtp.EmailBackend"},
}