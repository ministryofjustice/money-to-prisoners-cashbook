from django.conf import settings
from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.generic import RedirectView, TemplateView

from .views import (
    NewCreditsView, ProcessingCreditsView,
    ProcessedCreditsListView, ProcessedCreditsDetailView,
    SearchView,
)


class LandingView(TemplateView):
    template_name = 'landing.html'

    def get(self, request, *args, **kwargs):
        if not request.disbursements_available:
            return redirect('new-credits')
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            start_page_url=settings.START_PAGE_URL,
            **kwargs
        )


urlpatterns = [
    url(r'^$', login_required(LandingView.as_view()), name='home'),

    url(r'^new/$', NewCreditsView.as_view(), name='new-credits'),

    url(r'^processed/$', ProcessedCreditsListView.as_view(), name='processed-credits-list'),
    url(r'^processed/(?P<date>[0-9]{8})-(?P<user_id>[0-9]+)/$',
        ProcessedCreditsDetailView.as_view(), name='processed-credits-detail'),
    url(r'^processing/$', ProcessingCreditsView.as_view(), name='processing-credits'),

    url(r'^search/$', SearchView.as_view(), name='search'),
    url(r'^all/$', RedirectView.as_view(pattern_name='search', permanent=True)),
]
