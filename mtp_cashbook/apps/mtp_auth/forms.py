import logging

from django import forms
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _
from mtp_common.api import retrieve_all_pages_for_path
from mtp_common.user_admin.forms import SignUpForm
from oauthlib.oauth2 import OAuth2Error
from requests import RequestException

logger = logging.getLogger('mtp')

ACCOUNT_REQUEST_ROLE = 'prison-clerk'


class CashbookSignUpForm(SignUpForm):
    prison = forms.ChoiceField(label=_('Prison'), help_text=_('Enter the prison you’re based in'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        role_field = self.fields['role']
        role_field.initial = ACCOUNT_REQUEST_ROLE
        role_field.choices = ((ACCOUNT_REQUEST_ROLE, 'Business hub'),)
        prison_field = self.fields['prison']
        prison_field.choices = [['', _('Select a prison')]] + self.prison_choices

    @property
    def prison_choices(self):
        choices = cache.get('sign-up-prisons')
        if not choices:
            try:
                choices = retrieve_all_pages_for_path(self.api_session, '/prisons/', exclude_empty_prisons=True)
                choices = [[prison['nomis_id'], prison['name']] for prison in choices]
                cache.set('sign-up-prisons', choices, timeout=60 * 60 * 6)
            except (RequestException, OAuth2Error, ValueError):
                logger.exception('Could not look up prison list')
        return choices
