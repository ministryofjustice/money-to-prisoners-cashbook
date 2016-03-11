from django.conf.urls import url

from cashbook import views

urlpatterns = [
    url(r'^$', views.DashboardView.as_view(), name='dashboard'),
    url(r'^dashboard-batch-complete/$', views.DashboardView.as_view(),
        name='dashboard-batch-complete'),
    url(r'^dashboard-batch-incomplete/$', views.DashboardView.as_view(),
        name='dashboard-batch-incomplete'),

    url(r'^locked/$', views.TransactionsLockedView.as_view(), name='transactions-locked'),

    url(r'^batch/$', views.TransactionBatchListView.as_view(), name='transaction-list'),
    url(r'^batch-discard/$', views.transaction_batch_discard, name='transaction-discard'),

    url(r'^history/$', views.TransactionHistoryView.as_view(), name='transaction-history'),
    url(r'^history/search/$', views.TransactionHistoryView.as_view(show_search=True),
        name='transaction-history-search'),
]
