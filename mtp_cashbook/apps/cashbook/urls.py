from django.conf.urls import url
from django.views.generic import RedirectView

from .views import (
    NewCreditsView, ProcessingCreditsView,
    ProcessedCreditsListView, ProcessedCreditsDetailView,
    SearchView,
    CashbookFAQView,
    CashbookGetHelpView, CashbookGetHelpSuccessView,
)

urlpatterns = [
    url(r'^new/$', NewCreditsView.as_view(), name='new-credits'),

    url(r'^processed/$', ProcessedCreditsListView.as_view(), name='processed-credits-list'),
    url(r'^processed/(?P<date>[0-9]{8})-(?P<user_id>[0-9]+)/$',
        ProcessedCreditsDetailView.as_view(), name='processed-credits-detail'),
    url(r'^processing/$', ProcessingCreditsView.as_view(), name='processing-credits'),

    url(r'^search/$', SearchView.as_view(), name='search'),
    url(r'^all/$', RedirectView.as_view(pattern_name='search', permanent=True)),

    url(r'^cashbook/faq/$', CashbookFAQView.as_view(), name='cashbook-faq'),
    url(r'^cashbook/feedback/$', CashbookGetHelpView.as_view(), name='cashbook_submit_ticket'),
    url(r'^cashbook/feedback/success/$', CashbookGetHelpSuccessView.as_view(), name='cashbook_feedback_success'),
]
