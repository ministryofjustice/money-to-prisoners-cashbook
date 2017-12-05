import logging

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, TemplateView, View
from mtp_common.auth.api_client import get_api_session
from requests.exceptions import RequestException

from . import disbursements_available_required, forms as disbursement_forms

logger = logging.getLogger('mtp')


def build_view_url(request, url_name):
    url_name = '%s:%s' % (request.resolver_match.namespace, url_name)
    return reverse(url_name)


def clear_session_view(request):
    """
    View that clears the session and restarts the user flow.
    @param request: the HTTP request
    """
    DisbursementCompleteView.clear_session(request)
    return redirect(build_view_url(request, DisbursementStartView.url_name))


@method_decorator(login_required, name='dispatch')
@method_decorator(disbursements_available_required, name='dispatch')
class DisbursementView(View):
    previous_view = None
    payment_method = None
    final_step = False

    @classmethod
    def clear_session(cls, request):
        for view in cls.get_previous_views(cls):
            if hasattr(view, 'form_class'):
                view.form_class.delete_from_session(request)

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
        request.proposition_app = {
            'name': _('Digital disbursements'),
            'url': build_view_url(self.request, DisbursementStartView.url_name),
        }
        for view in self.get_previous_views(self):
            if not hasattr(view, 'form_class') or not view.is_form_enabled(self.valid_form_data):
                continue
            form = view.form_class.unserialise_from_session(
                request, self.valid_form_data)
            if form.is_valid():
                self.valid_form_data[view.url_name] = form.cleaned_data
            else:
                redirect_url = getattr(view, 'redirect_url_name', None) or view.url_name
                return redirect(build_view_url(self.request, redirect_url))
        return super().dispatch(request, *args, **kwargs)


class DisbursementFormView(DisbursementView, FormView):
    @classmethod
    def is_form_enabled(cls, previous_form_data):
        return True

    def get_context_data(self, **kwargs):
        if self.previous_view:
            kwargs['breadcrumbs_back'] = self.get_previous_url()
        context_data = super().get_context_data(**kwargs)
        if self.request.method == 'GET':
            form = self.form_class.unserialise_from_session(
                self.request, self.valid_form_data)
            if form.is_valid():
                # valid form found in session so restore it
                context_data['form'] = form
        return context_data

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['previous_form_data'] = self.valid_form_data
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
    redirect_url_name = DisbursementStartView.url_name
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
        kwargs['breadcrumbs_back'] = reverse('disbursements:prisoner')
        kwargs.update(**prisoner_details)
        return super().get_context_data(**kwargs)

    def get_success_url(self):
        return build_view_url(self.request, AmountView.url_name)


class AmountView(DisbursementFormView):
    url_name = 'amount'
    previous_view = PrisonerCheckView
    template_name = 'disbursements/amount.html'
    form_class = disbursement_forms.AmountForm

    def get_success_url(self):
        return build_view_url(self.request, SendingMethodView.url_name)


class SendingMethodView(DisbursementFormView):
    url_name = 'sending_method'
    previous_view = AmountView
    template_name = 'disbursements/sending-method.html'
    form_class = disbursement_forms.SendingMethodForm

    def get_success_url(self):
        return build_view_url(self.request, RecipientContactView.url_name)


class RecipientContactView(DisbursementFormView):
    url_name = 'recipient_contact'
    previous_view = SendingMethodView
    template_name = 'disbursements/recipient-contact.html'
    form_class = disbursement_forms.RecipientContactForm

    def get_success_url(self):
        sending_method = self.valid_form_data[SendingMethodView.url_name]
        if sending_method['sending_method'] == disbursement_forms.SENDING_METHOD.CHEQUE:
            return build_view_url(self.request, DetailsCheckView.url_name)
        else:
            return build_view_url(self.request, RecipientBankAccountView.url_name)


class RecipientBankAccountView(DisbursementFormView):
    url_name = 'recipient_bank_account'
    previous_view = RecipientContactView
    template_name = 'disbursements/recipient-bank-account.html'
    form_class = disbursement_forms.RecipientBankAccountForm

    @classmethod
    def is_form_enabled(cls, previous_form_data):
        sending_method = previous_form_data[SendingMethodView.url_name]
        return (
            sending_method['sending_method'] ==
            disbursement_forms.SENDING_METHOD.BANK_TRANSFER
        )

    def get_success_url(self):
        return build_view_url(self.request, DetailsCheckView.url_name)


class DetailsCheckView(DisbursementView, TemplateView):
    url_name = 'details_check'
    previous_view = RecipientBankAccountView
    template_name = 'disbursements/details-check.html'
    error_messages = {
        'connection': _('This service is currently unavailable')
    }

    def get_context_data(self, **kwargs):
        prisoner_details = self.valid_form_data[PrisonerView.url_name]
        recipient_contact_details = self.valid_form_data[RecipientContactView.url_name]
        sending_method_details = self.valid_form_data[SendingMethodView.url_name]
        amount_details = self.valid_form_data[AmountView.url_name]
        recipient_bank_details = self.valid_form_data.get(RecipientBankAccountView.url_name, {})
        kwargs['breadcrumbs_back'] = reverse('disbursements:recipient_contact')
        kwargs.update(**prisoner_details)
        kwargs.update(**recipient_contact_details)
        kwargs.update(**recipient_bank_details)
        kwargs.update(**sending_method_details)
        kwargs.update(**amount_details)

        if 'e' in self.request.GET:
            kwargs['errors'] = [self.error_messages.get(self.request.GET['e'])]
        return super().get_context_data(**kwargs)

    def get_success_url(self):
        return build_view_url(self.request, DisbursementCompleteView.url_name)


class DisbursementCompleteView(DisbursementView, TemplateView):
    url_name = 'complete'
    previous_view = DetailsCheckView
    template_name = 'disbursements/complete.html'
    final_step = True

    def get(self, request, *args, **kwargs):
        prisoner_details = self.valid_form_data[PrisonerView.url_name]
        recipient_contact_details = self.valid_form_data[RecipientContactView.url_name]
        sending_method_details = self.valid_form_data[SendingMethodView.url_name]
        amount_details = self.valid_form_data[AmountView.url_name]
        recipient_bank_details = self.valid_form_data.get(RecipientBankAccountView.url_name, {})

        try:
            api_session = get_api_session(request)
            recipient_data = {
                'first_name': recipient_contact_details['recipient_first_name'],
                'last_name': recipient_contact_details['recipient_last_name'],
                'line1': recipient_contact_details['address_line1'],
                'line2': recipient_contact_details['address_line2'],
                'city': recipient_contact_details['city'],
                'postcode': recipient_contact_details['postcode'],
                'email': recipient_contact_details['email'],
            }
            recipient_data.update(**recipient_bank_details)
            recipient = api_session.post(
                '/recipients/', json=recipient_data).json()

            disbursement_data = {
                'prisoner_number': prisoner_details['prisoner_number'],
                'prison': prisoner_details['prison'],
                'method': sending_method_details['sending_method'],
                'amount': amount_details['amount'],
                'recipient': recipient['id']
            }
            api_session.post('/disbursements/', json=disbursement_data)

            response = super().get(request, *args, **kwargs)
            self.clear_session(request)
            return response
        except RequestException:
            logger.exception('Failed to create disbursement')
            return redirect(
                '%s?e=connection' %
                build_view_url(self.request, self.previous_view.url_name)
            )
