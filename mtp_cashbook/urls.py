from django.conf.urls import patterns, include, url
from django.contrib.auth.decorators import login_required
from django.views.generic.base import TemplateView
from mtp_cashbook.apps.cashbook.views import TransactionBatchListView

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'mtp_cashbook.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^$', login_required(
            TemplateView.as_view(template_name='core/index.html')
        ), name='index'
    ),

    url(r'^batch/$',
            TransactionBatchListView.as_view(), name='transaction-list'
    ),

    url(r'^auth/', include('mtp_auth.urls', namespace='auth',)),
)
