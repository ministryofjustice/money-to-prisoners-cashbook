"""
Django settings for mtp_cashbook project.

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""
from functools import partial
import os
from os.path import abspath, dirname, join
import sys

BASE_DIR = dirname(dirname(abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))

get_project_dir = partial(join, BASE_DIR)

APP = 'cashbook'
ENVIRONMENT = os.environ.get('ENV', 'local')
APP_BUILD_DATE = os.environ.get('APP_BUILD_DATE')
APP_GIT_COMMIT = os.environ.get('APP_GIT_COMMIT')


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
SECRET_KEY = 'CHANGE_ME'
ALLOWED_HOSTS = []


# Application definition
INSTALLED_APPS = (
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.contenttypes',
    'django.contrib.auth',
)
PROJECT_APPS = (
    'mtp_common',
    'mtp_auth',
    'widget_tweaks',
    'cashbook',
    'zendesk_tickets',
    'mtp_user_admin',
)
INSTALLED_APPS += PROJECT_APPS


WSGI_APPLICATION = 'mtp_cashbook.wsgi.application'
ROOT_URLCONF = 'mtp_cashbook.urls'
MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'moj_auth.csrf.CsrfViewMiddleware',
    'moj_auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

HEALTHCHECKS = []
AUTODISCOVER_HEALTHCHECKS = True

# security tightening
# some overridden in prod/docker settings where SSL is ensured
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = False
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = False
CSRF_FAILURE_VIEW = 'moj_auth.csrf.csrf_failure'


# Database
DATABASES = {}


# Internationalization
LANGUAGE_CODE = 'en-gb'
TIME_ZONE = 'Europe/London'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_ROOT = 'static'
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    get_project_dir('assets'),
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            get_project_dir('templates'),
            get_project_dir('node_modules'),
            get_project_dir('../node_modules/mojular-templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'mtp_common.context_processors.analytics',
                'mtp_common.context_processors.app_environment',
            ],
        },
    },
]

# logging settings
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(asctime)s [%(levelname)s] %(message)s',
            'datefmt': '%Y-%m-%dT%H:%M:%S',
        },
        'elk': {
            '()': 'mtp_common.logging.ELKFormatter'
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple' if ENVIRONMENT == 'local' else 'elk',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        },
    },
    'root': {
        'level': 'WARNING',
        'handlers': ['console'],
    },
    'loggers': {
        'django.security.DisallowedHost': {
            'handlers': ['null'],
            'propagate': False,
        },
        'mtp': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': False,
        },
    },
}

# sentry exception handling
if os.environ.get('SENTRY_DSN'):
    INSTALLED_APPS = ('raven.contrib.django.raven_compat',) + INSTALLED_APPS
    RAVEN_CONFIG = {
        'dsn': os.environ['SENTRY_DSN'],
        'release': APP_GIT_COMMIT or 'unknown',
    }
    LOGGING['handlers']['sentry'] = {
        'level': 'ERROR',
        'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler'
    }
    LOGGING['root']['handlers'].append('sentry')
    LOGGING['loggers']['mtp']['handlers'].append('sentry')

TEST_RUNNER = 'mtp_common.test_utils.runner.TestRunner'

# authentication
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

MOJ_USER_MODEL = 'mtp_auth.models.MtpUser'

AUTHENTICATION_BACKENDS = (
    'moj_auth.backends.MojBackend',
)


def find_api_url():
    import socket
    import subprocess

    api_port = int(os.environ.get('API_PORT', '8000'))
    try:
        host_machine_ip = subprocess.check_output(['docker-machine', 'ip', 'default'],
                                                  stderr=subprocess.DEVNULL)
        host_machine_ip = host_machine_ip.decode('ascii').strip()
        with socket.socket() as sock:
            sock.connect((host_machine_ip, api_port))
    except (subprocess.CalledProcessError, OSError):
        host_machine_ip = 'localhost'
    return 'http://%s:%s' % (host_machine_ip, api_port)


API_CLIENT_ID = 'cashbook'
API_CLIENT_SECRET = os.environ.get('API_CLIENT_SECRET', 'cashbook')
API_URL = os.environ.get('API_URL', find_api_url())

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_URL = 'logout'

OAUTHLIB_INSECURE_TRANSPORT = True

REQUEST_PAGE_SIZE = 100
REQUEST_PAGE_DAYS = 5

GOOGLE_ANALYTICS_ID = os.environ.get('GOOGLE_ANALYTICS_ID', None)

ZENDESK_BASE_URL = 'https://ministryofjustice.zendesk.com'
ZENDESK_API_USERNAME = os.environ.get('ZENDESK_API_USERNAME', '')
ZENDESK_API_TOKEN = os.environ.get('ZENDESK_API_TOKEN', '')
ZENDESK_REQUESTER_ID = os.environ.get('ZENDESK_REQUESTER_ID', '')
ZENDESK_GROUP_ID = 26417927
ZENDESK_CUSTOM_FIELDS = {
    'referer': 26047167,
    'username': 29241738,
    'user_agent': 23791776,
    'contact_email': 30769508,
}

try:
    from .local import *  # noqa
except ImportError:
    pass
