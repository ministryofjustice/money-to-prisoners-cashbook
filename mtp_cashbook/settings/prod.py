""" Production settings

See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/
"""

import os


from mtp_cashbook.settings.base import *

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
