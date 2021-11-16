from django.conf.urls import url

from .views import CashbookSettingsView

urlpatterns = [
    url(r'^$', CashbookSettingsView.as_view(), name='settings'),
]
