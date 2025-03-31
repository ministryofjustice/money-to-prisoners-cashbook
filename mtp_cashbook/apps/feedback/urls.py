from django.urls import re_path

from feedback.views import GetHelpView, GetHelpSuccessView

urlpatterns = [
    re_path(r'^feedback/$', GetHelpView.as_view(), name='submit_ticket'),
    re_path(r'^feedback/success/$', GetHelpSuccessView.as_view(), name='feedback_success'),
]
