"""
Django settings for mtp_cashbook project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(APP_ROOT, ...)
import sys
import os
import json

from os.path import abspath, join, dirname

from django.conf import global_settings

here = lambda *x: join(abspath(dirname(__file__)), *x)
PROJECT_ROOT = here("..")
root = lambda *x: join(abspath(PROJECT_ROOT), *x)
with open(root('..', '.bowerrc')) as _bowerrc:
    _bower_path = json.load(_bowerrc)['directory']
bower_dir = lambda *x: join(_bower_path, *x)

sys.path.insert(0, os.path.join(root(), 'apps'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

SECRET_KEY = 'CHANGE_ME'

# Application definition

INSTALLED_APPS = (
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
)

PROJECT_APPS = (
    'moj_utils',
    'widget_tweaks',
    'mtp_auth',
    'cashbook'
)

INSTALLED_APPS += PROJECT_APPS

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'moj_auth.middleware.AuthenticationMiddleware',
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
    root('assets'),
    bower_dir(),
    bower_dir('mojular', 'assets'),
    bower_dir('govuk-template', 'assets'),
    bower_dir('money-to-prisoners-common', 'assets')
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            root('templates'),
            bower_dir('mojular', 'templates'),
            bower_dir('money-to-prisoners-common', 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'moj_utils.context_processors.debug',
                'moj_utils.context_processors.analytics',
            ],
        },
    },
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

DATABASES = {}


# AUTH
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

AUTH_USER_MODEL = 'mtp_auth.MtpUser'
MOJ_USER_MODEL = 'mtp_auth.models.MtpUser'

AUTHENTICATION_BACKENDS = (
    'moj_auth.backends.MojBackend',
)

API_CLIENT_ID = 'cashbook'
API_CLIENT_SECRET = os.environ.get('API_CLIENT_SECRET', 'cashbook')
API_URL = os.environ.get('API_URL', 'http://localhost:8000')

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'

OAUTHLIB_INSECURE_TRANSPORT = True


GOOGLE_ANALYTICS_ID = os.environ.get('GOOGLE_ANALYTICS_ID', None)

try:
    from .local import *  # noqa
except ImportError:
    pass
