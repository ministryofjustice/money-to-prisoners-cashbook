from django.conf.urls import url

from .views import TransactionBatchListView, TransactionsLockedView, \
    TransactionHistoryView, DashboardView

urlpatterns = [
    url(r'^locked/$', TransactionsLockedView.as_view(), name='transactions-locked'),
    url(r'^batch/$', TransactionBatchListView.as_view(), name='transaction-list'),
    url(r'^history/$', TransactionHistoryView.as_view(), name='transaction-history'),
    url(r'^$', DashboardView.as_view(), name='dashboard'),
]
