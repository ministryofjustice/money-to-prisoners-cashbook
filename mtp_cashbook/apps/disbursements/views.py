from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse, reverse_lazy
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic import FormView, TemplateView, View

from . import forms as disbursement_forms


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


@method_decorator(login_required, name='dispatch')
class DisbursementStartView(DisbursementView, TemplateView):
    url_name = 'start'
    template_name = 'disbursements/start.html'

    def get_success_url(self):
        return build_view_url(self.request, PrisonerView.url_name)


@method_decorator(login_required, name='dispatch')
class PrisonerView(DisbursementFormView):
    url_name = 'prisoner'
    previous_view = DisbursementStartView
    template_name = 'disbursements/prisoner.html'
    form_class = disbursement_forms.PrisonerForm

    def get_success_url(self):
        return build_view_url(self.request, PrisonerCheckView.url_name)


@method_decorator(login_required, name='dispatch')
class PrisonerCheckView(DisbursementView, TemplateView):
    url_name = 'prisoner_check'
    previous_view = PrisonerView
    template_name = 'disbursements/prisoner-check.html'

    def get_context_data(self, **kwargs):
        prisoner_details = self.valid_form_data[PrisonerView.url_name]
        kwargs.update(**prisoner_details)
        return super().get_context_data(**kwargs)

    def get_success_url(self):
        return build_view_url(self.request, AmountView.url_name)


@method_decorator(login_required, name='dispatch')
class AmountView(DisbursementFormView):
    url_name = 'amount'
    previous_view = PrisonerCheckView
    template_name = 'disbursements/amount.html'
    form_class = disbursement_forms.AmountForm

    def get_success_url(self):
        return build_view_url(self.request, SendingMethodView.url_name)


@method_decorator(login_required, name='dispatch')
class SendingMethodView(DisbursementFormView):
    url_name = 'sending_method'
    previous_view = AmountView
    template_name = 'disbursements/sending-method.html'
    form_class = disbursement_forms.SendingMethodForm

    def get_success_url(self):
        return build_view_url(self.request, RecipientContactView.url_name)


@method_decorator(login_required, name='dispatch')
class RecipientContactView(DisbursementFormView):
    url_name = 'recipient_contact'
    previous_view = SendingMethodView
    template_name = 'disbursements/recipient-contact.html'
    form_class = disbursement_forms.RecipientContactForm

    def get_success_url(self):
        return build_view_url(self.request, RecipientBankAccountView.url_name)


@method_decorator(login_required, name='dispatch')
class RecipientBankAccountView(DisbursementFormView):
    url_name = 'recipient_bank_account'
    previous_view = RecipientContactView
    template_name = 'disbursements/recipient-bank-account.html'
    form_class = disbursement_forms.RecipientBankAccountForm

    def get_success_url(self):
        return build_view_url(self.request, DetailsCheckView.url_name)


@method_decorator(login_required, name='dispatch')
class DetailsCheckView(DisbursementView, TemplateView):
    url_name = 'details_check'
    previous_view = RecipientBankAccountView
    template_name = 'disbursements/details-check.html'

    def get_context_data(self, **kwargs):
        prisoner_details = self.valid_form_data[PrisonerView.url_name]
        recipient_contact_details = self.valid_form_data[RecipientContactView.url_name]
        recipient_bank_details = self.valid_form_data[RecipientBankAccountView.url_name]
        sending_method_details = self.valid_form_data[SendingMethodView.url_name]
        amount_details = self.valid_form_data[AmountView.url_name]
        kwargs.update(**prisoner_details)
        kwargs.update(**recipient_contact_details)
        kwargs.update(**recipient_bank_details)
        kwargs.update(**sending_method_details)
        kwargs.update(**amount_details)
        return super().get_context_data(**kwargs)

    def get_success_url(self):
        return build_view_url(self.request, DisbursementCompleteView.url_name)


@method_decorator(login_required, name='dispatch')
class DisbursementCompleteView(DisbursementView, TemplateView):
    url_name = 'complete'
    previous_view = DetailsCheckView
    template_name = 'disbursements/complete.html'
    final_step = True

    def get_context_data(self, **kwargs):
        prisoner_details = self.valid_form_data[PrisonerView.url_name]
        recipient_contact_details = self.valid_form_data[RecipientContactView.url_name]
        recipient_bank_details = self.valid_form_data[RecipientBankAccountView.url_name]
        sending_method_details = self.valid_form_data[SendingMethodView.url_name]
        amount_details = self.valid_form_data[AmountView.url_name]
        kwargs.update(**prisoner_details)
        kwargs.update(**recipient_contact_details)
        kwargs.update(**recipient_bank_details)
        kwargs.update(**sending_method_details)
        kwargs.update(**amount_details)
        return super().get_context_data(**kwargs)
