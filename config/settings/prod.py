"""
prod.py
Staging Settings for Django Project
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env.str('POSTGRES_DB'),
        'USER': env.str('POSTGRES_USER'),
        'PASSWORD': env.str('POSTGRES_PASSWORD'),
        'HOST': env.str('DB_HOST'),
        'PORT': env.str('DB_PORT'),
    }
}

# Allowed hosts
ALLOWED_HOSTS = [
    'campus.makeaton.in',
    'ca.radr.in',
]

CSRF_TRUSTED_ORIGINS += [
    "https://ca.radr.in",
    "https://campus.makeaton.in",
]

# Additional CORS origins whitelist
CORS_ORIGIN_WHITELIST += [
    "https://ca.radr.in",
    "https://campus.makeaton.in",
]

CORS_ORIGIN_ALLOW_ALL = False

# Static and media files
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_BASE_URL = "media"
MEDIA_URL = '/media/'

STATIC_ROOT = BASE_DIR / "staticfiles"  # Replace with your staging static files directory
STATIC_URL = '/static/'

CACHE_TIMEOUT = 60 * 5  # 5 minutes
