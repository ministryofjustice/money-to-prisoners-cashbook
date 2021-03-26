from collections import OrderedDict
import logging

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _
from mtp_common.api import retrieve_all_pages_for_path
from mtp_common.user_admin.forms import SignUpForm
from oauthlib.oauth2 import OAuth2Error
from requests import RequestException
from zendesk_tickets.forms import BaseTicketForm

logger = logging.getLogger('mtp')

ACCOUNT_REQUEST_ROLE = 'prison-clerk'


class CashbookSignUpForm(SignUpForm, BaseTicketForm):
    prison = forms.ChoiceField(label=_('Prison'), help_text=_('Enter the prison you’re based in'))

    # Non form class variables
    cashbook_account_request_zendesk_subject = 'MTP for digital team - Digital Cashbook - Request for new staff account'
    zendesk_tags = ('feedback', 'mtp', 'cashbook', 'account_request', settings.ENVIRONMENT)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        role_field = self.fields['role']
        role_field.initial = ACCOUNT_REQUEST_ROLE
        role_field.choices = ((ACCOUNT_REQUEST_ROLE, 'Business hub'),)
        prison_field = self.fields['prison']
        prison_field.choices = [['', _('Select a prison')]] + list(self.prison_choices.items())

    @property
    def prison_choices(self):
        choices = cache.get('sign-up-prisons')
        if not choices:
            try:
                choices = retrieve_all_pages_for_path(self.api_session, '/prisons/', exclude_empty_prisons=True)
                choices = OrderedDict([[prison['nomis_id'], prison['name']] for prison in choices])
                cache.set('sign-up-prisons', choices, timeout=60 * 60 * 6)
            except (RequestException, OAuth2Error, ValueError):
                logger.exception('Could not look up prison list')
        return choices

    def user_already_requested_account(self):
        try:
            response = self.api_session.get(
                'requests/',
                params={
                    'username': self.cleaned_data['username'],
                    'role__name': self.cleaned_data['role']
                }
            )
            return response.json().get('count', 0) > 0
        except (RequestException, OAuth2Error, ValueError):
            logger.exception('Could not look up access requests')
            self.add_error(None, _('This service is currently unavailable'))

    def clean(self):
        if self.is_valid() and self.user_already_requested_account():
            return self.submit_ticket(
                self.request,
                subject=self.cashbook_account_request_zendesk_subject,
                tags=self.zendesk_tags,
                ticket_template_name='mtp_common/user_admin/new-account-request-ticket.txt',
                requester_email=self.cleaned_data['email'],
                extra_context={'prison_name': self.prison_choices.get(self.cleaned_data['prison'], 'N/A')}
            )
        return super().clean()
