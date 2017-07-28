from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$',
        views.DisbursementStartView.as_view(),
        name=views.DisbursementStartView.url_name),
    url(r'^prisoner/$',
        views.PrisonerView.as_view(),
        name=views.PrisonerView.url_name),
    url(r'^prisoner_check/$',
        views.PrisonerCheckView.as_view(),
        name=views.PrisonerCheckView.url_name),
    url(r'^amount/$',
        views.AmountView.as_view(),
        name=views.AmountView.url_name),
    url(r'^recipient_contact/$',
        views.RecipientContactView.as_view(),
        name=views.RecipientContactView.url_name),
    url(r'^recipient_bank_account/$',
        views.RecipientBankAccountView.as_view(),
        name=views.RecipientBankAccountView.url_name),
    url(r'^details_check/$',
        views.DetailsCheckView.as_view(),
        name=views.DetailsCheckView.url_name),
    url(r'^complete/$',
        views.DisbursementCompleteView.as_view(),
        name=views.DisbursementCompleteView.url_name),
    url(r'^clear-session/$', views.clear_session_view, name='clear_session'),
    url(r'^processed/$',
        views.ProcessedDisbursementsView.as_view(),
        name=views.ProcessedDisbursementsView.url_name),
    url(r'^all/$',
        views.AllDisbursementsView.as_view(),
        name=views.AllDisbursementsView.url_name),
]
