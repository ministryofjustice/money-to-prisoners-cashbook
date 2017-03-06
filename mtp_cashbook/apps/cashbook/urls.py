from django.conf import settings
from django.conf.urls import url
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import redirect

from .views import (
    CreditBatchListView, CreditsLockedView, CreditHistoryView, DashboardView,
    inactive_password_change_view, NewCreditsView, AllCreditsView
)
from .views_training import ServiceOverview, Training


def dashboard_view(request):
    nomis_integration_available = settings.NOMIS_API_AVAILABLE and any((
        prison['nomis_id'] in settings.NOMIS_API_PRISONS
        for prison in request.user.user_data.get('prisons', [])
    ))

    if nomis_integration_available:
        return redirect(reverse_lazy('new-credits'))
    return DashboardView.as_view()(request)


urlpatterns = [
    url(r'^$', dashboard_view, name='dashboard'),
    url(r'^dashboard-batch-complete/$', DashboardView.as_view(),
        name='dashboard-batch-complete'),
    url(r'^dashboard-batch-incomplete/$', DashboardView.as_view(),
        name='dashboard-batch-incomplete'),
    url(r'^dashboard-batch-discard/$', DashboardView.as_view(discard_batch=True),
        name='dashboard-batch-discard'),
    url(r'^dashboard-unlocked-payments/$', DashboardView.as_view(),
        name='dashboard-unlocked-payments'),

    url(r'^locked/$', CreditsLockedView.as_view(), name='credits-locked'),

    url(r'^batch/$', CreditBatchListView.as_view(), name='credit-list'),

    url(r'^history/$', CreditHistoryView.as_view(), name='credit-history'),

    url(r'^service-overview/(?:(?P<page>[^/]+)/)?$', ServiceOverview.as_view(), name='service-overview'),
    url(r'^training/(?:(?P<page>[^/]+)/)?$', Training.as_view(), name='training'),

    url(r'^inactive_password_change/$', inactive_password_change_view, name='inactive_password_change'),

    url(r'^new/$', NewCreditsView.as_view(), name='new-credits'),
    url(r'^all/$', AllCreditsView.as_view(), name='all-credits'),
]
