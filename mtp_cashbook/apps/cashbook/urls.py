from django.conf.urls import patterns, url

from .views import TransactionBatchListView, TransactionsLockedView, DashboardView


urlpatterns = patterns('',
    url(r'^locked/$', TransactionsLockedView.as_view(), name='transactions-locked'),
    url(r'^batch/$', TransactionBatchListView.as_view(), name='transaction-list'),
    url(r'^$', DashboardView.as_view(), name='dashboard'),
)
