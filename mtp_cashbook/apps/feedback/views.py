from django.conf import settings
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from mtp_common.views import GetHelpView as BaseGetHelpView, GetHelpSuccessView as BaseGetHelpSuccessView

from feedback.forms import PrisonTicketForm


class GetHelpView(BaseGetHelpView):
    form_class = PrisonTicketForm
    success_url = reverse_lazy('feedback_success')
    ticket_subject = 'MTP Cashbook Feedback'
    ticket_tags = ['feedback', 'mtp', 'cashbook', settings.ENVIRONMENT]

    def get_context_data(self, **kwargs):
        kwargs['get_help_title'] = _('Contact us')
        return super().get_context_data(**kwargs)


class GetHelpSuccessView(BaseGetHelpSuccessView):
    def get_context_data(self, **kwargs):
        kwargs['get_help_title'] = _('Contact us')
        return super().get_context_data(**kwargs)
