from django.conf import settings
from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import redirect
from django.views.generic import TemplateView

from .views import (
    NewCreditsView, ProcessedCreditsListView, ChangeNotificationView,
    ProcessingCreditsView, ProcessedCreditsDetailView, AllCreditsView,
)


@login_required
def dashboard_view(request):
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


class LandingView(TemplateView):
    template_name = 'cashbook/landing.html'

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            start_page_url=settings.START_PAGE_URL,
            **kwargs
        )


urlpatterns = [
    url(r'^$', dashboard_view, name='dashboard'),
    url(r'^landing/$', LandingView.as_view(), name='landing'),

    url(r'^change-notification/$', ChangeNotificationView.as_view(), name='change-notification'),
    url(r'^new/$', NewCreditsView.as_view(), name='new-credits'),
    url(r'^all/$', AllCreditsView.as_view(), name='all-credits'),
    url(r'^processed/$', ProcessedCreditsListView.as_view(), name='processed-credits-list'),
    url(r'^processed/(?P<date>[0-9]{8})-(?P<user_id>[0-9]+)/$',
        ProcessedCreditsDetailView.as_view(), name='processed-credits-detail'),
    url(r'^processing/$', ProcessingCreditsView.as_view(), name='processing-credits'),
]
