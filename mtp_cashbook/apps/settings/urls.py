from django.urls import re_path

from .views import CashbookSettingsView, ChangeCreditNoticeEmailsView

urlpatterns = [
    re_path(r'^$', CashbookSettingsView.as_view(), name='settings'),
    re_path(r'^credit-notice-emails/$', ChangeCreditNoticeEmailsView.as_view(), name='credit-notice-emails'),
]
