from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import redirect

from .utils import nomis_integration_available
from .views import (
    CreditBatchListView, CreditsLockedView, CreditHistoryView, DashboardView,
    inactive_password_change_view, NewCreditsView, ProcessedCreditsListView,
    ChangeNotificationView, ProcessingCreditsView
)
from .views_training import ServiceOverview, Training


@login_required
def dashboard_view(request):
    if nomis_integration_available(request):
        cookie_content = request.COOKIES.get('change-notification-read')
        if cookie_content:
            users_notified = cookie_content.split(',')
            if request.user.username in users_notified:
                return redirect(reverse_lazy('new-credits'))
        response = redirect(reverse_lazy('change-notification'))
        response.set_cookie(
            'change-notification-read',
            ','.join([cookie_content, request.user.username])
            if cookie_content else request.user.username,
            max_age=5 * 365 * 24 * 60 * 60
        )
        return response
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

    url(r'^change-notification/$', ChangeNotificationView.as_view(), name='change-notification'),
    url(r'^new/$', NewCreditsView.as_view(), name='new-credits'),
    url(r'^processed/$', ProcessedCreditsListView.as_view(), name='processed-credits-list'),
    url(r'^processing/$', ProcessingCreditsView.as_view(), name='processing-credits'),
]
