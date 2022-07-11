import logging

from django.contrib import messages
from django.http import Http404, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.functional import cached_property
from django.utils.http import is_safe_url
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, TemplateView
from mtp_common import nomis
from mtp_common.analytics import genericised_pageview
from mtp_common.api import retrieve_all_pages_for_path
from mtp_common.auth.api_client import get_api_session
from mtp_common.auth.exceptions import HttpNotFoundError
from mtp_common.utils import format_currency
from requests.exceptions import HTTPError, RequestException

from disbursements import forms as disbursement_forms
from disbursements.utils import get_disbursement_viability, find_addresses
from feedback.views import GetHelpView, GetHelpSuccessView
from mtp_cashbook.misc_views import BaseView
from mtp_cashbook.utils import one_month_ago

logger = logging.getLogger('mtp')


class DisbursementView(BaseView, TemplateView):
    """
    Base view for all disbursement views
    """
    title = None
    url_name = None

    @classmethod
    def url(cls, **kwargs):
        return reverse('disbursements:%s' % cls.url_name, kwargs=kwargs)

    @cached_property
    def api_session(self):
        return get_api_session(self.request)

    def dispatch(self, request, **kwargs):
        request.proposition_app = {
            'sub_app': 'disbursements',
            'name': _('Digital disbursements'),
            'url': StartView.url(),
            'help_url': DisbursementGetHelpView.url(),
        }
        return super().dispatch(request, **kwargs)

    def get_template_names(self):
        if self.template_name:
            return [self.template_name]
        if self.url_name:
            return ['disbursements/%s.html' % self.url_name]
        return super().get_template_names()

    def get_context_data(self, **kwargs):
        try:
            response = self.api_session.get(
                'disbursements/', params={'resolution': 'pending', 'limit': 1}
            ).json()
            kwargs['pending_disbursement_count'] = response['count']
            kwargs['confirm_tab_suffix'] = ' (%s)' % kwargs['pending_disbursement_count']
        except RequestException:
            pass
        return super().get_context_data(**kwargs)


class BasePagedView(DisbursementView):
    """
    Base template view used in multi-page flows
    """
    previous_view = None
    next_view = None

    @classmethod
    def as_view(cls, **initkwargs):
        if cls.previous_view:
            cls.previous_view.next_view = cls
        return super().as_view(**initkwargs)

    @classmethod
    def get_previous_views(cls):
        if cls.previous_view:
            yield from cls.previous_view.get_previous_views()
            yield cls.previous_view

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.valid_form_data = {}
        self.redirect_success_url = None

    def get_valid_form_data(self, view):
        return self.valid_form_data.get(view.form_class.__name__, {})

    def dispatch(self, request, **kwargs):
        for view in self.get_previous_views():
            if not issubclass(view, BasePagedFormView):
                continue
            form = view.form_class.unserialise_from_session(request, self.valid_form_data)
            if form.is_valid():
                self.valid_form_data[view.form_class.__name__] = form.cleaned_data
            elif view.is_form_required(self.valid_form_data):
                return redirect(view.url(**kwargs))
        next_url = request.GET.get('next')
        if is_safe_url(next_url, allowed_hosts={request.get_host()}):
            self.redirect_success_url = next_url
        return super().dispatch(request, **kwargs)

    def get_context_data(self, **kwargs):
        if self.previous_view:
            kwargs['breadcrumbs_back'] = self.previous_view.url(**self.kwargs)
        return super().get_context_data(**kwargs)

    def get_success_url(self):
        if self.redirect_success_url:
            return self.redirect_success_url
        if self.next_view:
            return self.next_view.url()


class BasePagedFormView(BasePagedView, FormView):
    """
    Base form view used in multi-page flows
    """

    @classmethod
    def is_form_required(cls, valid_form_data):
        return True

    def get_form(self, form_class=None):
        if self.request.method == 'GET':
            form = self.form_class.unserialise_from_session(self.request, self.valid_form_data)
            if form.is_valid():
                # valid form found in session so restore it
                return form
        return super().get_form(form_class)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        # valid form so save in session
        form.serialise_data(self.request.session, form.cleaned_data)
        return super().form_valid(form)


class BaseConfirmationView(DisbursementView, FormView):
    """
    Base form view for yes/no steps which store no information
    """
    form_class = disbursement_forms.ConfirmationForm
    alternate_success_url = None

    def form_valid(self, form):
        if form.cleaned_data['confirmation'] == 'no':
            if self.alternate_success_url:
                return redirect(self.alternate_success_url)
            form.add_error('confirmation', form['confirmation'].field.error_messages['cannot_proceed'])
            return self.form_invalid(form)
        return super().form_valid(form)


# creation flow


class SendingMethodView(BasePagedFormView):
    title = _('How the prisoner wants to send money')
    url_name = 'sending_method'
    form_class = disbursement_forms.SendingMethodForm

    def form_valid(self, form):
        if form.cleaned_data['method'] == disbursement_forms.SENDING_METHOD.CHEQUE:
            RecipientBankAccountView.form_class.delete_from_session(self.request)
        return super().form_valid(form)


class PrisonerView(BasePagedFormView):
    title = _('Send money out for this prisoner')
    url_name = 'prisoner'
    previous_view = SendingMethodView
    form_class = disbursement_forms.PrisonerForm


class PrisonerCheckView(BaseConfirmationView, BasePagedView):
    title = _('Confirm prisoner details')
    url_name = 'prisoner_check'
    previous_view = PrisonerView
    alternate_success_url = reverse_lazy('disbursements:clear_disbursement')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form['confirmation'].label = _('Does the name above match that on the paper form?')
        return form

    def get_context_data(self, **kwargs):
        kwargs.update(self.get_valid_form_data(PrisonerView))
        return super().get_context_data(**kwargs)


class AmountView(BasePagedFormView):
    title = _('Enter amount')
    url_name = 'amount'
    previous_view = PrisonerCheckView
    form_class = disbursement_forms.AmountForm

    def get_nomis_balances(self):
        try:
            form_data = self.get_valid_form_data(PrisonerView)
            return nomis.get_account_balances(form_data['prison'], form_data['prisoner_number'])
        except (RequestException, KeyError):
            pass

    def get(self, request, **kwargs):
        if request.is_ajax():
            balances = self.get_nomis_balances()
            if balances:
                return JsonResponse({
                    'spends': format_currency(balances['spends']),
                    'cash': format_currency(balances['cash']),
                    'savings': format_currency(balances['savings']),
                })
            else:
                raise Http404('Balance not available')
        return super().get(request, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['nomis_balances'] = self.get_nomis_balances()
        return kwargs


class RecipientContactView(BasePagedFormView):
    title = _('Enter recipient details')
    url_name = 'recipient_contact'
    previous_view = AmountView
    form_class = disbursement_forms.RecipientContactForm


class RecipientPostcodeView(BasePagedFormView):
    title = _('Enter recipient address')
    url_name = 'recipient_postcode'
    previous_view = RecipientContactView
    form_class = disbursement_forms.RecipientPostcodeForm

    @classmethod
    def is_form_required(cls, valid_form_data):
        return False


class RecipientAddressView(BasePagedFormView):
    title = _('Enter recipient address')
    url_name = 'recipient_address'
    previous_view = RecipientPostcodeView
    form_class = disbursement_forms.RecipientAddressForm

    def get_context_data(self, **kwargs):
        kwargs['postcode'] = self.get_valid_form_data(
            RecipientPostcodeView).get('postcode')

        if kwargs['postcode'] and not self.redirect_success_url:
            kwargs['address_picker'] = True
            kwargs['addresses'] = find_addresses(kwargs['postcode'])
        return super().get_context_data(**kwargs)

    def get_success_url(self):
        form_data = self.get_valid_form_data(SendingMethodView)
        if form_data.get('method') == disbursement_forms.SENDING_METHOD.CHEQUE:
            self.next_view = RemittanceDescriptionView
        else:
            self.next_view = RecipientBankAccountView
        return super().get_success_url()


class RecipientBankAccountView(BasePagedFormView):
    title = _('Enter recipient bank details')
    url_name = 'recipient_bank_account'
    previous_view = RecipientAddressView
    form_class = disbursement_forms.RecipientBankAccountForm

    @classmethod
    def is_form_required(cls, valid_form_data):
        return (
            valid_form_data[SendingMethodView.form_class.__name__]['method'] ==
            disbursement_forms.SENDING_METHOD.BANK_TRANSFER
        )

    def get_context_data(self, **kwargs):
        kwargs.update(self.get_valid_form_data(RecipientContactView))
        return super().get_context_data(**kwargs)


class RemittanceDescriptionView(BasePagedFormView):
    title = _('Add a payment description')
    url_name = 'remittance_description'
    previous_view = RecipientBankAccountView
    form_class = disbursement_forms.RemittanceDescriptionForm

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form_data = self.get_valid_form_data(PrisonerView)
        form.set_prisoner_name(form_data.get('prisoner_name'))
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form_data = self.get_valid_form_data(SendingMethodView)
        if form_data.get('method') == disbursement_forms.SENDING_METHOD.CHEQUE:
            context['breadcrumbs_back'] = RecipientBankAccountView.previous_view.url()

        form_data = self.get_valid_form_data(PrisonerView)
        if form_data.get('prisoner_name'):
            context['prisoner_name'] = form_data['prisoner_name']

        field = disbursement_forms.RemittanceDescriptionForm.base_fields['remittance_description']
        context['remittance_description_character_count'] = field.max_length
        return context


class DetailsCheckView(BaseConfirmationView, BasePagedView):
    title = _('Check payment details')
    url_name = 'details_check'
    previous_view = RemittanceDescriptionView

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form['confirmation'].label = _('Do the details above match those on the paper form?')
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for view in self.get_previous_views():
            if issubclass(view, BasePagedFormView):
                context.update(self.get_valid_form_data(view))
        return context


class HandoverView(BasePagedView):
    title = _('Hand over the paper form for confirmation')
    url_name = 'handover'
    previous_view = DetailsCheckView
    error_messages = {
        'connection': _('Payment not created due to technical error, try again soon')
    }

    def get_context_data(self, **kwargs):
        if 'e' in self.request.GET:
            kwargs['errors'] = [self.error_messages.get(self.request.GET['e'])]
        return super().get_context_data(**kwargs)


class CreatedView(BasePagedView):
    title = _('Disbursement request saved')
    url_name = 'created'
    previous_view = HandoverView
    http_method_names = ['post']

    @classmethod
    def clear_disbursement(cls, request):
        view = StartView
        for view in cls.get_previous_views():
            if issubclass(view, BasePagedFormView):
                view.form_class.delete_from_session(request)
        return redirect(view.url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        del context['breadcrumbs_back']
        return context

    def post(self, request):
        disbursement_data = {}
        for view in self.get_previous_views():
            if issubclass(view, BasePagedFormView):
                disbursement_data.update(**self.get_valid_form_data(view))
        if disbursement_data['recipient_type'] == 'person':
            disbursement_data['recipient_is_company'] = False
        elif disbursement_data['recipient_type'] == 'company':
            disbursement_data['recipient_is_company'] = True
            disbursement_data['recipient_last_name'] = disbursement_data['recipient_company_name']
        del disbursement_data['recipient_type']
        del disbursement_data['recipient_company_name']
        del disbursement_data['prisoner_dob']
        if 'remittance' in disbursement_data:
            del disbursement_data['remittance']
        try:
            self.api_session.post('/disbursements/', json=disbursement_data)
            logger.info('Created disbursement')
        except RequestException:
            logger.exception('Failed to create disbursement')
            return redirect('%s?e=connection' % self.previous_view.url())

        self.clear_disbursement(self.request)

        return self.get(request)


# confirmation flow


class PendingListView(DisbursementView):
    title = _('Confirm payments')
    url_name = 'pending_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['disbursements'] = retrieve_all_pages_for_path(
            self.api_session, 'disbursements/', resolution='pending'
        )
        context['disbursements'] += retrieve_all_pages_for_path(
            self.api_session, 'disbursements/', resolution='preconfirmed'
        )
        context['pending_count'] = len(context['disbursements'])

        for disbursement in context['disbursements']:
            disbursement.update(
                **get_disbursement_viability(self.request, disbursement)
            )

        return context


class PendingDetailView(BaseConfirmationView):
    title = _('Check payment details')
    url_name = 'pending_detail'

    error_messages = {
        'connection': _('Payment not confirmed due to technical error, try again soon'),
        'invalid': _(
            'There was a problem with some of the payment details, please '
            'check them again and fix if necessary'
        )
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.disbursement = None
        self.disbursement_viability = {}

    def dispatch(self, request, **kwargs):
        try:
            self.disbursement = self.api_session.get(
                'disbursements/{pk}/'.format(pk=kwargs['pk'])
            ).json()
        except HttpNotFoundError:
            raise Http404('Disbursement not found', {'disbursement_id': kwargs['pk']})
        self.disbursement_viability = get_disbursement_viability(self.request, self.disbursement)
        return super().dispatch(request, **kwargs)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form['confirmation'].label = _('Do the details above match those on the paper form?')
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        reject_form = disbursement_forms.RejectDisbursementForm()

        context.update(
            reject_form=reject_form,
            breadcrumbs_back=PendingListView.url(),
            disbursement=self.disbursement,
            **self.disbursement_viability
        )

        return context

    def create_nomis_transaction(self, form):
        disbursement = self.disbursement
        try:
            nomis_response = nomis.create_transaction(
                prison_id=disbursement['prison'],
                prisoner_number=disbursement['prisoner_number'],
                amount=disbursement['amount'],
                record_id='d%s' % disbursement['id'],
                description='Sent to {recipient_first_name} {recipient_last_name}'.format(
                    recipient_first_name=disbursement['recipient_first_name'],
                    recipient_last_name=disbursement['recipient_last_name'],
                ).replace('  ', ' '),
                transaction_type='RELA',
                retries=1
            )
            return nomis_response['id']
        except HTTPError as e:
            if e.response.status_code == 409:
                logger.warning(
                    'Disbursement %(disbursement_id)s was already present in NOMIS',
                    {'disbursement_id': disbursement['id']}
                )
                return None
            elif e.response.status_code >= 500:
                logger.error(
                    'Disbursement %(disbursement_id)s could not be made as NOMIS is unavailable',
                    {'disbursement_id': disbursement['id']}
                )
                form.add_error(None, self.error_messages['connection'])
            else:
                logger.warning(
                    'Disbursement %(disbursement_id)s is invalid',
                    {'disbursement_id': disbursement['id']}
                )
                form.add_error(None, self.error_messages['invalid'])
        except RequestException:
            logger.exception(
                'Disbursement %(disbursement_id)s could not be made as NOMIS is unavailable',
                {'disbursement_id': disbursement['id']}
            )
            form.add_error(None, self.error_messages['connection'])

    def form_valid(self, form):
        if form.cleaned_data['confirmation'] == 'no':
            if self.alternate_success_url:
                return redirect(self.alternate_success_url)
            form.add_error('confirmation', form['confirmation'].field.error_messages['cannot_proceed'])
            return self.form_invalid(form)

        if not self.disbursement_viability['viable']:
            form.add_error(None, self.error_messages['invalid'])
            return self.form_invalid(form)

        nomis_transaction_id = None
        try:
            if self.disbursement['resolution'] != 'preconfirmed':
                self.api_session.post(
                    'disbursements/actions/preconfirm/',
                    json={'disbursement_ids': [self.disbursement['id']]}
                )

            nomis_transaction_id = self.create_nomis_transaction(form)
        except HTTPError as e:
            if e.response.status_code == 409:
                form.add_error(None, self.error_messages['invalid'])
            else:
                raise e

        if form.is_valid():
            update = {'id': self.disbursement['id']}
            url_suffix = '?nomis_transaction_id='
            if nomis_transaction_id:
                update['nomis_transaction_id'] = nomis_transaction_id
                url_suffix = '%s%s' % (url_suffix, nomis_transaction_id)
            self.api_session.post(
                'disbursements/actions/confirm/',
                json=[update]
            )
            logger.info('Confirmed disbursement %(id)d', update)
            return redirect(ConfirmedView.url() + url_suffix)

        self.api_session.post(
            'disbursements/actions/reset/',
            json={'disbursement_ids': [self.disbursement['id']]}
        )

        return self.form_invalid(form)

    def get_reject_url(self):
        return RejectPendingView.url(**self.kwargs)


class ConfirmedView(DisbursementView):
    title = _('Payment confirmation')
    url_name = 'confirmed'

    def get_context_data(self, **kwargs):
        if 'nomis_transaction_id' not in self.request.GET:
            raise Http404('This view should not be accessed directly')
        kwargs['nomis_transaction_id'] = self.request.GET['nomis_transaction_id']
        return super().get_context_data(**kwargs)


class RejectPendingView(DisbursementView, FormView):
    url_name = 'pending_reject'
    form_class = disbursement_forms.RejectDisbursementForm
    success_url = reverse_lazy('disbursements:%s' % PendingListView.url_name)
    http_method_names = ['post']

    def form_valid(self, form):
        try:
            form.reject(self.request, self.kwargs['pk'])
            messages.info(self.request, _('Payment request cancelled.'))
        except RequestException:
            logger.exception(
                'Could not reject disbursement %(disbursement_id)s',
                {'disbursement_id': self.kwargs['pk']}
            )
            messages.error(self.request, _('Unable to cancel payment request.'))
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _('Unable to cancel payment request.'))
        return super().form_valid(form)


class BaseEditFormView(BasePagedFormView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.disbursement = None

    def dispatch(self, request, **kwargs):
        try:
            self.disbursement = self.api_session.get(
                'disbursements/{pk}/'.format(pk=kwargs['pk'])
            ).json()
        except HttpNotFoundError:
            raise Http404('Disbursement not found', {'disbursement_id': kwargs['pk']})
        for view in list(self.get_previous_views()) + [self.__class__]:
            if not issubclass(view, BasePagedFormView) or not view.is_form_required(self.valid_form_data):
                continue
            disbursement_data = self.disbursement.copy()
            view.form_class.serialise_data(request.session, disbursement_data)
            form = view.form_class.unserialise_from_session(request, self.valid_form_data)
            if form.is_valid():
                self.valid_form_data[view.form_class.__name__] = form.cleaned_data
        return super().dispatch(request, **kwargs)

    def get_template_names(self):
        return ['disbursements/%s.html' % self.url_name.replace('update_', '')]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumbs_back'] = self.get_success_url()
        return context

    def form_valid(self, form):
        disbursement_data = self.get_update_payload(form)
        update = {}
        for field in disbursement_data:
            if disbursement_data[field] != self.disbursement.get(field):
                update[field] = disbursement_data[field]
        if 'prisoner_number' in update:
            update['prison'] = disbursement_data['prison']
        if update:
            self.api_session.patch(
                'disbursements/{pk}/'.format(**self.kwargs),
                json=update
            )
        return super().form_valid(form)

    def get_update_payload(self, form):
        update = {}
        for field in form.base_fields:
            update[field] = form.cleaned_data[field]
        return update

    def get_success_url(self):
        CreatedView.clear_disbursement(self.request)
        return PendingDetailView.url(**self.kwargs)


class UpdateSendingMethodView(BaseEditFormView, SendingMethodView):
    url_name = 'update_sending_method'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.require_bank_account = False

    def form_valid(self, form):
        self.require_bank_account = form.cleaned_data['method'] == disbursement_forms.SENDING_METHOD.BANK_TRANSFER
        return super().form_valid(form)

    def get_update_payload(self, form):
        if self.require_bank_account:
            return {}
        payload = super().get_update_payload(form)
        payload.update(account_number='', sort_code='', roll_number='')
        return payload

    def get_success_url(self):
        if self.require_bank_account:
            return UpdateRecipientBankAccountView.url(**self.kwargs)
        return super().get_success_url()


class UpdatePrisonerView(BaseEditFormView, PrisonerView):
    url_name = 'update_prisoner'
    previous_view = UpdateSendingMethodView

    def get_update_payload(self, form):
        payload = super().get_update_payload(form)
        payload['prison'] = form.cleaned_data['prison']
        return payload


class UpdateAmountView(BaseEditFormView, AmountView):
    url_name = 'update_amount'
    previous_view = UpdatePrisonerView


class UpdateRecipientContactView(BaseEditFormView, RecipientContactView):
    url_name = 'update_recipient_contact'
    previous_view = UpdateAmountView

    def get_update_payload(self, form):
        update = super().get_update_payload(form)
        if update['recipient_type'] == 'person':
            update['recipient_is_company'] = False
        elif update['recipient_type'] == 'company':
            update['recipient_is_company'] = True
            update['recipient_first_name'] = ''
            update['recipient_last_name'] = update['recipient_company_name']
        del update['recipient_type']
        del update['recipient_company_name']
        return update


class UpdateRecipientAddressView(BaseEditFormView, RecipientAddressView):
    url_name = 'update_recipient_address'
    previous_view = UpdateRecipientContactView


class UpdateRecipientBankAccountView(BaseEditFormView, RecipientBankAccountView):
    url_name = 'update_recipient_bank_account'
    previous_view = UpdateRecipientAddressView

    def get_update_payload(self, form):
        payload = super().get_update_payload(form)
        payload.update(method=disbursement_forms.SENDING_METHOD.BANK_TRANSFER)
        return payload


class UpdateRemittanceDescriptionView(BaseEditFormView, RemittanceDescriptionView):
    url_name = 'update_remittance_description'
    previous_view = UpdateRecipientBankAccountView

    def get_update_payload(self, form):
        update = super().get_update_payload(form)
        del update['remittance']
        return update


# misc views


class StartView(DisbursementView):
    url_name = 'start'
    get_success_url = reverse_lazy('disbursements:clear_disbursement')

    def get_context_data(self, **kwargs):
        kwargs['confirmed_disbursement_count'] = sum(
            self.api_session.get(
                'disbursements/', params={'resolution': resolution, 'limit': 1}
            ).json().get('count', 0)
            for resolution in ['confirmed', 'sent']
        )
        return super().get_context_data(**kwargs)


class PaperFormsView(DisbursementView):
    url_name = 'paper-forms'


class SearchView(DisbursementView, FormView):
    title = _('Payments made')
    url_name = 'search'
    form_class = disbursement_forms.SearchForm

    def get_initial(self):
        initial = super().get_initial()
        initial.update({
            'date__gte': one_month_ago().strftime('%d/%m/%Y'),
        })

        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['google_analytics_pageview'] = genericised_pageview(
            self.request, self.title
        )
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        request_data = self.get_initial()
        request_data.update(self.request.GET.dict())
        kwargs['data'] = request_data
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        context = self.get_context_data(form=form)
        context['disbursements'] = form.get_object_list()
        return self.render_to_response(context)

    get = FormView.post


class DisbursementHelpView(DisbursementView):
    sub_navigation_links = [
        {
            'key': 'process_overview',
            'href': reverse_lazy('disbursements:process-overview'),
            'text': _('How it works'),
        },
        {
            'key': 'submit_ticket',
            'href': reverse_lazy('disbursements:submit_ticket'),
            'text': _('Contact us'),
        },
    ]

    @classmethod
    def make_sub_navigation_links(cls, active_key):
        return [
            dict(link, active=link['key'] == active_key)
            for link in cls.sub_navigation_links
        ]


class ProcessOverview(DisbursementHelpView):
    url_name = 'process-overview'

    def get_context_data(self, **kwargs):
        kwargs['sub_navigation_links'] = self.make_sub_navigation_links('process_overview')
        return super().get_context_data(**kwargs)


class TrackInvoice(DisbursementHelpView):
    url_name = 'track-invoice'

    def get_context_data(self, **kwargs):
        kwargs.setdefault('breadcrumbs_back', reverse('disbursements:process-overview'))
        kwargs['sub_navigation_links'] = self.make_sub_navigation_links('process_overview')
        return super().get_context_data(**kwargs)


class KioskInstructions(DisbursementHelpView):
    url_name = 'kiosk-instructions'

    def get_context_data(self, **kwargs):
        kwargs.setdefault('breadcrumbs_back', f"{reverse('disbursements:process-overview')}#section-fill-form")
        kwargs['sub_navigation_links'] = self.make_sub_navigation_links('process_overview')
        return super().get_context_data(**kwargs)


class DisbursementGetHelpView(DisbursementHelpView, GetHelpView):
    url_name = 'submit_ticket'
    base_template_name = 'disbursements/base.html'
    template_name = 'disbursements/feedback/submit_feedback.html'
    success_url = reverse_lazy('disbursements:feedback_success')

    def get_context_data(self, **kwargs):
        kwargs['sub_navigation_links'] = self.make_sub_navigation_links('submit_ticket')
        return super().get_context_data(**kwargs)


class DisbursementGetHelpSuccessView(DisbursementHelpView, GetHelpSuccessView):
    url_name = 'feedback_success'
    base_template_name = 'disbursements/base.html'
    template_name = 'disbursements/feedback/success.html'

    def get_context_data(self, **kwargs):
        kwargs['sub_navigation_links'] = self.make_sub_navigation_links('submit_ticket')
        return super().get_context_data(**kwargs)
