from django.core.urlresolvers import reverse, reverse_lazy
from django.shortcuts import redirect
from django.views.generic import FormView, TemplateView, View

from . import forms as disbursement_forms

TEST_DISBURSEMENTS = [
    {
        'date': '15/01/17',
        'name': 'Bob Jones',
        'account_number': '12345555',
        'sort_code': '12-35-61',
        'email': 'bob.jones@smail.com',
        'address': {
            'line1': '44 Evering Road',
            'line2': 'Stoke Newington',
            'city': 'London',
            'postcode': 'N16 7SR'
        },
        'account': 'spends',
        'amount': '£20.00',
        'prisoner_number': 'A1345XZ',
        'prisoner_name': 'Gareth Barlow',
        'processed_by': 'Tina Wilson',
        'nomis_transaction_id': '1637589323-1'
    },
    {
        'date': '15/01/17',
        'name': 'John Smith',
        'account_number': '46465757',
        'sort_code': '21-08-34',
        'email': 'john.smitch@coldmail.com',
        'address': {
            'line1': '12 Down Street',
            'line2': '',
            'city': 'Nottingham',
            'postcode': 'NG1 6UP'
        },
        'account': 'private',
        'amount': '£30.00',
        'prisoner_number': 'A8494HJ',
        'prisoner_name': 'Jason Orange',
        'processed_by': 'Tina Wilson',
        'nomis_transaction_id': '1637589094-1'
    },
    {
        'date': '16/01/17',
        'name': 'James Buck',
        'account_number': '83954674',
        'sort_code': '08-36-94',
        'email': 'james.buck@smail.com',
        'address': {
            'line1': '70 Petty France',
            'line2': '',
            'city': 'London',
            'postcode': 'SW1H 9EX'
        },
        'account': 'spends',
        'amount': '£15.00',
        'prisoner_number': 'A0947AD',
        'prisoner_name': 'Marcus Owen',
        'processed_by': 'Tina Wilson',
        'nomis_transaction_id': '1637589738-1'
    },
    {
        'date': '17/01/17',
        'name': 'Lucy Williams',
        'account_number': '28424315',
        'sort_code': '12-09-09',
        'email': 'lwilliams87@nowmail.com',
        'address': {
            'line1': '55 The Street',
            'line2': 'Banningham',
            'city': 'Cambridgeshire',
            'postcode': 'C18 9PR'
        },
        'account': 'private',
        'amount': '£40.00',
        'prisoner_number': 'A1678PO',
        'prisoner_name': 'Robert Williams',
        'processed_by': 'Daniel McGuinness',
        'nomis_transaction_id': '1637589897-1'
    },
    {
        'date': '17/01/17',
        'name': 'Diana Ross',
        'account_number': '19067822',
        'sort_code': '13-73-92',
        'email': 'dfross@btinternet.com',
        'address': {
            'line1': 'The Vicarage',
            'line2': 'Burgh',
            'city': 'Suffolk',
            'postcode': 'IP13 6SU'
        },
        'account': 'spends',
        'amount': '£20.00',
        'prisoner_number': 'A0925LK',
        'prisoner_name': 'Howard Donald',
        'processed_by': 'Daniel McGuinness',
        'nomis_transaction_id': '1637589894-1'
    },
]


def build_view_url(request, url_name):
    url_name = '%s:%s' % (request.resolver_match.namespace, url_name)
    return reverse(url_name)


def clear_session_view(request):
    """
    View that clears the session and restarts the user flow.
    @param request: the HTTP request
    """
    request.session.flush()
    return redirect(build_view_url(request, DisbursementStartView.url_name))


class DisbursementView(View):
    previous_view = None
    payment_method = None
    final_step = False

    @classmethod
    def get_previous_views(cls, view):
        if view.previous_view:
            yield from cls.get_previous_views(view.previous_view)
            yield view.previous_view

    def get_previous_url(self):
        return build_view_url(self.request, self.previous_view.url_name)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.valid_form_data = {}

    def dispatch(self, request, *args, **kwargs):
        for view in self.get_previous_views(self):
            if not hasattr(view, 'form_class') or not view.is_form_enabled():
                continue
            form = view.form_class.unserialise_from_session(request)
            if form.is_valid():
                self.valid_form_data[view.url_name] = form.cleaned_data
            else:
                return redirect(build_view_url(self.request, view.url_name))
        return super().dispatch(request, *args, **kwargs)


class DisbursementFormView(DisbursementView, FormView):
    @classmethod
    def is_form_enabled(cls):
        return True

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        if self.request.method == 'GET':
            form = self.form_class.unserialise_from_session(self.request)
            if form.is_valid():
                # valid form found in session so restore it
                context_data['form'] = form
        return context_data

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        # save valid form to session
        form.serialise_to_session()
        return super().form_valid(form)


class DisbursementStartView(DisbursementView, TemplateView):
    url_name = 'start'
    template_name = 'disbursements/start.html'

    def get_success_url(self):
        return build_view_url(self.request, PrisonerView.url_name)


class PrisonerView(DisbursementFormView):
    url_name = 'prisoner'
    previous_view = DisbursementStartView
    template_name = 'disbursements/prisoner.html'
    form_class = disbursement_forms.PrisonerForm

    def get_success_url(self):
        return build_view_url(self.request, PrisonerCheckView.url_name)


class PrisonerCheckView(DisbursementView, TemplateView):
    url_name = 'prisoner_check'
    previous_view = PrisonerView
    template_name = 'disbursements/prisoner-check.html'

    def get_context_data(self, **kwargs):
        prisoner_details = self.valid_form_data[PrisonerView.url_name]
        kwargs.update(**prisoner_details)
        return super().get_context_data(**kwargs)

    def get_success_url(self):
        return build_view_url(self.request, PrisonerAccountView.url_name)


class PrisonerAccountView(DisbursementFormView):
    url_name = 'prisoner-account'
    previous_view = PrisonerCheckView
    template_name = 'disbursements/prisoner-account.html'
    form_class = disbursement_forms.PrisonerAccountForm

    def get_success_url(self):
        return build_view_url(self.request, AmountView.url_name)


class AmountView(DisbursementFormView):
    url_name = 'amount'
    previous_view = PrisonerAccountView
    template_name = 'disbursements/amount.html'
    form_class = disbursement_forms.AmountForm

    def get_success_url(self):
        return build_view_url(self.request, RecipientContactView.url_name)


class RecipientContactView(DisbursementFormView):
    url_name = 'recipient_contact'
    previous_view = AmountView
    template_name = 'disbursements/recipient-contact.html'
    form_class = disbursement_forms.RecipientContactForm

    def get_success_url(self):
        return build_view_url(self.request, RecipientBankAccountView.url_name)


class RecipientBankAccountView(DisbursementFormView):
    url_name = 'recipient_bank_account'
    previous_view = RecipientContactView
    template_name = 'disbursements/recipient-bank-account.html'
    form_class = disbursement_forms.RecipientBankAccountForm

    def get_success_url(self):
        return build_view_url(self.request, DetailsCheckView.url_name)


class DetailsCheckView(DisbursementView, TemplateView):
    url_name = 'details_check'
    previous_view = RecipientBankAccountView
    template_name = 'disbursements/details-check.html'

    def get_context_data(self, **kwargs):
        prisoner_details = self.valid_form_data[PrisonerView.url_name]
        recipient_contact_details = self.valid_form_data[RecipientContactView.url_name]
        recipient_bank_details = self.valid_form_data[RecipientBankAccountView.url_name]
        prisoner_account_details = self.valid_form_data[PrisonerAccountView.url_name]
        amount_details = self.valid_form_data[AmountView.url_name]
        kwargs.update(**prisoner_details)
        kwargs.update(**recipient_contact_details)
        kwargs.update(**recipient_bank_details)
        kwargs.update(**prisoner_account_details)
        kwargs.update(**amount_details)
        return super().get_context_data(**kwargs)

    def get_success_url(self):
        return build_view_url(self.request, DisbursementCompleteView.url_name)


class DisbursementCompleteView(DisbursementView, TemplateView):
    url_name = 'complete'
    previous_view = DetailsCheckView
    template_name = 'disbursements/complete.html'
    final_step = True

    def get_context_data(self, **kwargs):
        prisoner_details = self.valid_form_data[PrisonerView.url_name]
        recipient_contact_details = self.valid_form_data[RecipientContactView.url_name]
        recipient_bank_details = self.valid_form_data[RecipientBankAccountView.url_name]
        prisoner_account_details = self.valid_form_data[PrisonerAccountView.url_name]
        amount_details = self.valid_form_data[AmountView.url_name]
        kwargs.update(**prisoner_details)
        kwargs.update(**recipient_contact_details)
        kwargs.update(**recipient_bank_details)
        kwargs.update(**prisoner_account_details)
        kwargs.update(**amount_details)
        return super().get_context_data(**kwargs)


class ProcessedDisbursementsView(FormView):
    url_name = 'processed'
    template_name = 'disbursements/processed-disbursements.html'
    form_class = disbursement_forms.FilterProcessedDisbursementsListForm

    def get_context_data(self, **kwargs):
        kwargs['disbursements'] = TEST_DISBURSEMENTS
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        return super().form_valid(form)


class AllDisbursementsView(FormView):
    url_name = 'all'
    form_class = disbursement_forms.FilterAllDisbursementsForm
    template_name = 'disbursements/all.html'
    success_url = reverse_lazy(url_name)

    def get_context_data(self, **kwargs):
        kwargs['disbursements'] = [TEST_DISBURSEMENTS[1]]
        kwargs['search_term'] = self.request.GET['search']
        return super().get_context_data(**kwargs)
