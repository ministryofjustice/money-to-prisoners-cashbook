from django.conf.urls import url

from .views import TransactionBatchListView, TransactionsLockedView, \
    TransactionHistoryView, DashboardView, transaction_batch_discard

urlpatterns = [
    url(r'^locked/$', TransactionsLockedView.as_view(), name='transactions-locked'),
    url(r'^batch/$', TransactionBatchListView.as_view(), name='transaction-list'),
    url(r'^batch-discard/$', transaction_batch_discard, name='transaction-discard'),
    url(r'^history/$', TransactionHistoryView.as_view(), name='transaction-history'),
    url(r'^$', DashboardView.as_view(), name='dashboard'),
]
