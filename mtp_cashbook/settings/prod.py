"""
Production/Docker settings
See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/
"""
from mtp_cashbook.settings.base import *  # noqa

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', False)

ALLOWED_HOSTS = [
    'localhost',
    '.dsd.io',
    '.service.gov.uk'
]

OAUTHLIB_INSECURE_TRANSPORT = os.environ.get(
    'OAUTHLIB_INSECURE_TRANSPORT', False
)

# security tightening
SECURE_SSL_REDIRECT = True  # also done at nginx level
SECURE_HSTS_SECONDS = 300
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
