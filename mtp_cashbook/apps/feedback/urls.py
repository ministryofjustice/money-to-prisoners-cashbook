from django.conf.urls import url

from feedback.views import GetHelpView, GetHelpSuccessView

urlpatterns = [
    url(r'^feedback/$', GetHelpView.as_view(), name='submit_ticket'),
    url(r'^feedback/success/$', GetHelpSuccessView.as_view(), name='feedback_success'),
]
