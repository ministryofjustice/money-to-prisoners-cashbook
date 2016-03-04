from django import forms
from django.utils.translation import ugettext_lazy as _
from zendesk_tickets.forms import BaseTicketForm


class FeedbackForm(BaseTicketForm):
    ticket_content = forms.CharField(
        label=_('Enter your feedback or any questions you have about this service.'),
        widget=forms.Textarea
    )
    contact_email = forms.EmailField(
        label=_('Your email address'), required=False
    )

    def submit_ticket(self, request, subject, tags,
                      ticket_template_name, extra_context={}):
        extra_context = dict(extra_context, **{
            'user_agent': request.META.get('HTTP_USER_AGENT')
        })
        return super().submit_ticket(request, subject, tags,
                                     ticket_template_name, extra_context)
