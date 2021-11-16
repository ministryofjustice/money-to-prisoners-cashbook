from django.conf.urls import url

from .views import CashbookSettingsView, ChangeCreditNoticeEmailsView

urlpatterns = [
    url(r'^$', CashbookSettingsView.as_view(), name='settings'),
    url(r'^credit-notice-emails/$', ChangeCreditNoticeEmailsView.as_view(), name='credit-notice-emails'),
]
