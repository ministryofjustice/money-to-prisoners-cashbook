from django.urls import re_path

from . import views

app_name = 'disbursements'
urlpatterns = [
    re_path(r'^$', views.StartView.as_view(),
        name=views.StartView.url_name),

    # creation flow
    re_path(r'^sending_method/$', views.SendingMethodView.as_view(),
        name=views.SendingMethodView.url_name),
    re_path(r'^prisoner/$', views.PrisonerView.as_view(),
        name=views.PrisonerView.url_name),
    re_path(r'^prisoner_check/$', views.PrisonerCheckView.as_view(),
        name=views.PrisonerCheckView.url_name),
    re_path(r'^amount/$', views.AmountView.as_view(),
        name=views.AmountView.url_name),
    re_path(r'^recipient_contact/$', views.RecipientContactView.as_view(),
        name=views.RecipientContactView.url_name),
    re_path(r'^recipient_postcode/$', views.RecipientPostcodeView.as_view(),
        name=views.RecipientPostcodeView.url_name),
    re_path(r'^recipient_address/$', views.RecipientAddressView.as_view(),
        name=views.RecipientAddressView.url_name),
    re_path(r'^recipient_bank_account/$', views.RecipientBankAccountView.as_view(),
        name=views.RecipientBankAccountView.url_name),
    re_path(r'^remittance_description/$', views.RemittanceDescriptionView.as_view(),
        name=views.RemittanceDescriptionView.url_name),
    re_path(r'^details_check/$', views.DetailsCheckView.as_view(),
        name=views.DetailsCheckView.url_name),
    re_path(r'^handover/$', views.HandoverView.as_view(),
        name=views.HandoverView.url_name),
    re_path(r'^created/$', views.CreatedView.as_view(),
        name=views.CreatedView.url_name),
    re_path(r'^clear/$', views.CreatedView.clear_disbursement, name='clear_disbursement'),

    # confirmation flow
    re_path(r'^pending/$', views.PendingListView.as_view(),
        name=views.PendingListView.url_name),
    re_path(r'^pending/(?P<pk>\d+)/$', views.PendingDetailView.as_view(),
        name=views.PendingDetailView.url_name),
    re_path(r'^pending/(?P<pk>\d+)/reject/$', views.RejectPendingView.as_view(),
        name=views.RejectPendingView.url_name),
    re_path(r'^pending/(?P<pk>\d+)/sending_method/$', views.UpdateSendingMethodView.as_view(),
        name=views.UpdateSendingMethodView.url_name),
    re_path(r'^pending/(?P<pk>\d+)/prisoner/$', views.UpdatePrisonerView.as_view(),
        name=views.UpdatePrisonerView.url_name),
    re_path(r'^pending/(?P<pk>\d+)/amount/$', views.UpdateAmountView.as_view(),
        name=views.UpdateAmountView.url_name),
    re_path(r'^pending/(?P<pk>\d+)/recipient_contact/$', views.UpdateRecipientContactView.as_view(),
        name=views.UpdateRecipientContactView.url_name),
    re_path(r'^pending/(?P<pk>\d+)/recipient_address/$', views.UpdateRecipientAddressView.as_view(),
        name=views.UpdateRecipientAddressView.url_name),
    re_path(r'^pending/(?P<pk>\d+)/recipient_bank_account/$', views.UpdateRecipientBankAccountView.as_view(),
        name=views.UpdateRecipientBankAccountView.url_name),
    re_path(r'^pending/(?P<pk>\d+)/remittance_description/$', views.UpdateRemittanceDescriptionView.as_view(),
        name=views.UpdateRemittanceDescriptionView.url_name),
    re_path(r'^confirmed/$', views.ConfirmedView.as_view(),
        name=views.ConfirmedView.url_name),

    re_path(r'^paper-forms/$', views.PaperFormsView.as_view(),
        name=views.PaperFormsView.url_name),

    re_path(r'^search/$', views.SearchView.as_view(),
        name=views.SearchView.url_name),

    re_path(r'^process-overview/$', views.ProcessOverview.as_view(),
        name=views.ProcessOverview.url_name),
    re_path(r'^track-invoice/$', views.TrackInvoice.as_view(),
        name=views.TrackInvoice.url_name),
    re_path(r'^kiosk-instructions/$', views.KioskInstructions.as_view(),
        name=views.KioskInstructions.url_name),

    re_path(r'^feedback/$', views.DisbursementGetHelpView.as_view(),
        name=views.DisbursementGetHelpView.url_name),
    re_path(r'^feedback/success/$', views.DisbursementGetHelpSuccessView.as_view(),
        name=views.DisbursementGetHelpSuccessView.url_name),
]
