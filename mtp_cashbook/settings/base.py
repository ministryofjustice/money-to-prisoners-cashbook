"""
Django settings for mtp_cashbook project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import sys
import os

from django.conf import global_settings
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True


SECRET_KEY = 'CHANGE_ME'

# Application definition

INSTALLED_APPS = (
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
)

PROJECT_APPS = (
    'core',
    'mtp_auth'
)

INSTALLED_APPS += PROJECT_APPS

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'mtp_auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'mtp_cashbook.urls'

WSGI_APPLICATION = 'mtp_cashbook.wsgi.application'


# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-gb'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_ROOT = 'static'
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'assets')
]

TEMPLATE_DIRS = [
    os.path.join(BASE_DIR, 'templates')
]

# Sane logging defaults
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'WARN',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'propagate': True,
            'level': 'WARN',
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        }
    }
}

TEMPLATE_CONTEXT_PROCESSORS = global_settings.TEMPLATE_CONTEXT_PROCESSORS + (
    'mtp_cashbook.apps.core.context_processors.debug',
    'django.core.context_processors.request'
)

DATABASES = {}


# AUTH
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'

AUTH_USER_MODEL = 'mtp_auth.MtpUser'

AUTHENTICATION_BACKENDS = (
    'mtp_auth.backends.MtpBackend',
)

API_CLIENT_ID = 'cashbook'
API_CLIENT_SECRET = os.environ.get('API_CLIENT_SECRET', 'cashbook')
API_URL = os.environ.get('API_URL', 'http://localhost:8000')

LOGIN_URL = 'auth:login'
LOGIN_REDIRECT_URL = 'index'

OAUTHLIB_INSECURE_TRANSPORT = True

try:
    from .local import *
except ImportError:
    pass
