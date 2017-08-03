from django.conf import settings
from django.conf.urls import url
from django.views.generic import TemplateView

from .views import (
    NewCreditsView, ProcessedCreditsListView, ChangeNotificationView,
    ProcessingCreditsView, ProcessedCreditsDetailView, AllCreditsView,
)


class LandingView(TemplateView):
    template_name = 'cashbook/landing.html'

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            start_page_url=settings.START_PAGE_URL,
            **kwargs
        )


urlpatterns = [
    url(r'^$', LandingView.as_view(), name='home'),
    url(r'^change-notification/$', ChangeNotificationView.as_view(), name='change-notification'),
    url(r'^new/$', NewCreditsView.as_view(), name='new-credits'),
    url(r'^all/$', AllCreditsView.as_view(), name='all-credits'),
    url(r'^processed/$', ProcessedCreditsListView.as_view(), name='processed-credits-list'),
    url(r'^processed/(?P<date>[0-9]{8})-(?P<user_id>[0-9]+)/$',
        ProcessedCreditsDetailView.as_view(), name='processed-credits-detail'),
    url(r'^processing/$', ProcessingCreditsView.as_view(), name='processing-credits'),
]
