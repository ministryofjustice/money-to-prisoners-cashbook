from django.urls import re_path
from django.views.generic import RedirectView

from .views import (
    NewCreditsView, ProcessingCreditsView,
    ProcessedCreditsListView, ProcessedCreditsDetailView,
    SearchView,
    CashbookFAQView,
    CashbookGetHelpView, CashbookGetHelpSuccessView,
)

urlpatterns = [
    re_path(r'^new/$', NewCreditsView.as_view(), name='new-credits'),

    re_path(r'^processed/$', ProcessedCreditsListView.as_view(), name='processed-credits-list'),
    re_path(
        r'^processed/(?P<date>[0-9]{8})-(?P<user_id>[0-9]+)/$',
        ProcessedCreditsDetailView.as_view(),
        name='processed-credits-detail',
    ),
    re_path(r'^processing/$', ProcessingCreditsView.as_view(), name='processing-credits'),

    re_path(r'^search/$', SearchView.as_view(), name='search'),
    re_path(r'^all/$', RedirectView.as_view(pattern_name='search', permanent=True)),

    re_path(r'^cashbook/faq/$', CashbookFAQView.as_view(), name='cashbook-faq'),
    re_path(r'^cashbook/feedback/$', CashbookGetHelpView.as_view(), name='cashbook_submit_ticket'),
    re_path(r'^cashbook/feedback/success/$', CashbookGetHelpSuccessView.as_view(), name='cashbook_feedback_success'),
]
