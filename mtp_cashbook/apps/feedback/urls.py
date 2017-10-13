from django.conf import settings
from django.conf.urls import url
from django.core.urlresolvers import reverse_lazy
from zendesk_tickets import views

from .forms import PrisonTicketForm

ticket_subject = 'MTP Cashbook Feedback'
ticket_tags = ['feedback', 'mtp', 'cashbook', settings.ENVIRONMENT]
urlpatterns = [
    url(r'^feedback/$', views.ticket,
        {
            'form_class': PrisonTicketForm,
            'template_name': 'mtp_common/feedback/submit_feedback.html',
            'success_redirect_url': reverse_lazy('feedback_success'),
            'subject': ticket_subject,
            'tags': ticket_tags,
        }, name='submit_ticket'),
    url(r'^feedback/success/$', views.success,
        {
            'template_name': 'mtp_common/feedback/success.html',
        }, name='feedback_success'),
]
