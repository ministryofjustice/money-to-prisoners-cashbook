from collections import OrderedDict
import logging

from django import forms
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
    cashbook_account_request_zendesk_subject = 'Request for access to cashbook'
    # TODO check these tags with laurie
    zendesk_tags = ('mtp', 'cashbook', 'account-request')

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
        # TODO Also, is it worth adding a unique_together definition for username/role fields?
        response = self.api_session.get(
            'requests/',
            params={
                'username': self.cleaned_data['username'],
                'role__name': self.cleaned_data['role']
            }
        )
        return response.json().get('count', 0) > 0

    def clean(self):
        if self.user_already_requested_account():
            return self.submit_ticket(
                self.request,
                subject=self.cashbook_account_request_zendesk_subject,
                tags=self.zendesk_tags,
                ticket_template_name='mtp_common/user_admin/new-account-request-ticket.txt',
                requester_email=self.cleaned_data['email'],
                extra_context={'prison_name': self.prison_choices.get(self.cleaned_data['prison'], 'N/A')}
            )
        return super().clean()
