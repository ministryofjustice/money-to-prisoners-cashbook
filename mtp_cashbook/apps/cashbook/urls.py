from django.conf.urls import url

from .views import TransactionBatchListView, TransactionsLockedView, \
    TransactionHistoryView, DashboardView, transaction_batch_discard

urlpatterns = [
    url(r'^$', DashboardView.as_view(), name='dashboard'),
    url(r'^dashboard-batch-complete/$', DashboardView.as_view(),
        name='dashboard-batch-complete'),
    url(r'^dashboard-batch-incomplete/$', DashboardView.as_view(),
        name='dashboard-batch-incomplete'),

    url(r'^locked/$', TransactionsLockedView.as_view(), name='transactions-locked'),

    url(r'^batch/$', TransactionBatchListView.as_view(), name='transaction-list'),
    url(r'^batch-discard/$', transaction_batch_discard, name='transaction-discard'),

    url(r'^history/$', TransactionHistoryView.as_view(), name='transaction-history'),
]
