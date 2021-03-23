from django import forms
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from mtp_common.auth.exceptions import Unauthorized
from slumber.exceptions import HttpClientError
from zendesk_tickets.forms import EmailTicketForm


class PrisonTicketForm(EmailTicketForm):

    ticket_content = forms.CharField(
        label=_('Please give details'),
        widget=forms.Textarea,
    )

    contact_email = forms.EmailField(
        label=_('Your email address'), required=True,
    )

    def submit_ticket(self, request, subject, tags, ticket_template_name, **kwargs):
        try:
            accessible_prisons = sorted(prison['name'] for prison in request.user.user_data.get('prisons', []))
            if accessible_prisons:
                subject = '%(subject)s (%(accessible_prisons)s)' % {
                    'subject': subject,
                    'accessible_prisons': ', '.join(accessible_prisons)
                }
            prison_tags = list(map(slugify, accessible_prisons))
        except (KeyError, HttpClientError, Unauthorized):
            prison_tags = []
        super().submit_ticket(request, subject, tags + prison_tags, ticket_template_name, **kwargs)
