from .base import *
import os

DEBUG = False
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',') 
 
SECURE_SSL_REDIRECT = True 
SESSION_COOKIE_SECURE = True 
CSRF_COOKIE_SECURE = True 
SECURE_HSTS_SECONDS = 31536000 
SECURE_HSTS_INCLUDE_SUBDOMAINS = True 
SECURE_HSTS_PRELOAD = True
 
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage' 

MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        "OPTIONS": {
            "host": os.environ.get("EMAIL_HOST", "localhost"),
            "port": int(os.environ.get("EMAIL_PORT", 25)),
        },
    },
}