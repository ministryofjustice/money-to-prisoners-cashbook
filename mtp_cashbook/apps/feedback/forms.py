from django.utils.text import slugify
from mtp_common.auth.exceptions import Unauthorized
from slumber.exceptions import HttpClientError
from zendesk_tickets.forms import EmailTicketForm


class PrisonTicketForm(EmailTicketForm):
    def submit_ticket(self, request, subject, tags, ticket_template_name, **kwargs):
        try:
            accessible_prisons = sorted(prison['name'] for prison in request.user.user_data.get('prisons', []))
            subject = '%(subject)s (%(accessible_prisons)s)' % {
                'subject': subject,
                'accessible_prisons': ', '.join(accessible_prisons)
            }
            tags.extend(map(slugify, accessible_prisons))
        except (KeyError, HttpClientError, Unauthorized):
            pass
        super().submit_ticket(request, subject, tags, ticket_template_name, **kwargs)
