from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.StartView.as_view(),
        name=views.StartView.url_name),

    # creation flow
    url(r'^sending_method/$', views.SendingMethodView.as_view(),
        name=views.SendingMethodView.url_name),
    url(r'^prisoner/$', views.PrisonerView.as_view(),
        name=views.PrisonerView.url_name),
    url(r'^prisoner_check/$', views.PrisonerCheckView.as_view(),
        name=views.PrisonerCheckView.url_name),
    url(r'^amount/$', views.AmountView.as_view(),
        name=views.AmountView.url_name),
    url(r'^recipient_contact/$', views.RecipientContactView.as_view(),
        name=views.RecipientContactView.url_name),
    url(r'^recipient_bank_account/$', views.RecipientBankAccountView.as_view(),
        name=views.RecipientBankAccountView.url_name),
    url(r'^remittance_description/$', views.RemittanceDescriptionView.as_view(),
        name=views.RemittanceDescriptionView.url_name),
    url(r'^details_check/$', views.DetailsCheckView.as_view(),
        name=views.DetailsCheckView.url_name),
    url(r'^handover/$', views.HandoverView.as_view(),
        name=views.HandoverView.url_name),
    url(r'^created/$', views.CreatedView.as_view(),
        name=views.CreatedView.url_name),
    url(r'^clear/$', views.CreatedView.clear_disbursement, name='clear_disbursement'),

    # confirmation flow
    url(r'^pending/$', views.PendingListView.as_view(),
        name=views.PendingListView.url_name),
    url(r'^pending/(?P<pk>\d+)/$', views.PendingDetailView.as_view(),
        name=views.PendingDetailView.url_name),
    url(r'^pending/(?P<pk>\d+)/reject/$', views.RejectPendingView.as_view(),
        name=views.RejectPendingView.url_name),
    url(r'^pending/(?P<pk>\d+)/sending_method/$', views.UpdateSendingMethodView.as_view(),
        name=views.UpdateSendingMethodView.url_name),
    url(r'^pending/(?P<pk>\d+)/prisoner/$', views.UpdatePrisonerView.as_view(),
        name=views.UpdatePrisonerView.url_name),
    url(r'^pending/(?P<pk>\d+)/amount/$', views.UpdateAmountView.as_view(),
        name=views.UpdateAmountView.url_name),
    url(r'^pending/(?P<pk>\d+)/recipient_contact/$', views.UpdateRecipientContactView.as_view(),
        name=views.UpdateRecipientContactView.url_name),
    url(r'^pending/(?P<pk>\d+)/recipient_bank_account/$', views.UpdateRecipientBankAccountView.as_view(),
        name=views.UpdateRecipientBankAccountView.url_name),
    url(r'^confirmed/$', views.ConfirmedView.as_view(),
        name=views.ConfirmedView.url_name),

    url(r'^paper-forms/$', views.PaperFormsView.as_view(),
        name=views.PaperFormsView.url_name),

    url(r'^search/$', views.SearchView.as_view(),
        name=views.SearchView.url_name),

    url(r'^process-overview/$', views.ProcessOverview.as_view(),
        name=views.ProcessOverview.url_name),
    url(r'^feedback/$', views.DisbursementGetHelpView.as_view(),
        name=views.DisbursementGetHelpView.url_name),
    url(r'^feedback/success/$', views.DisbursementGetHelpSuccessView.as_view(),
        name=views.DisbursementGetHelpSuccessView.url_name),
]
