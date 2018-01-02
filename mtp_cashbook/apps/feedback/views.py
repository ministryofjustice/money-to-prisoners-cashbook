from django.conf import settings
from django.urls import reverse_lazy
from mtp_common.views import GetHelpView as BaseGetHelpView, GetHelpSuccessView as BaseGetHelpSuccessView

from feedback.forms import PrisonTicketForm


class GetHelpView(BaseGetHelpView):
    form_class = PrisonTicketForm
    success_url = reverse_lazy('feedback_success')
    ticket_subject = 'MTP Cashbook Feedback'
    ticket_tags = ['feedback', 'mtp', 'cashbook', settings.ENVIRONMENT]


class GetHelpSuccessView(BaseGetHelpSuccessView):
    pass
