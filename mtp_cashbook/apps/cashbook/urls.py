from django.conf.urls import patterns, url

from .views import TransactionBatchListView, DashboardView


urlpatterns = patterns('',
    url(r'^batch/$', TransactionBatchListView.as_view(), name='transaction-list'),
    url(r'^$', DashboardView.as_view(), name='dashboard'),
)
