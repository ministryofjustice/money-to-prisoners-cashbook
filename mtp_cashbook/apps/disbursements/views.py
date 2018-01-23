import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.utils.http import is_safe_url
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, TemplateView
from mtp_common.api import retrieve_all_pages_for_path
from mtp_common.auth.api_client import get_api_session
from mtp_common.auth.exceptions import HttpNotFoundError
from mtp_common import nomis
from requests.exceptions import HTTPError, RequestException

from cashbook.templatetags.currency import currency
from disbursements import disbursements_available_required, forms as disbursement_forms
from disbursements.utils import get_disbursement_viability
from feedback.views import GetHelpView, GetHelpSuccessView

logger = logging.getLogger('mtp')


class BaseView(TemplateView):
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

    @method_decorator(login_required)
    @method_decorator(disbursements_available_required)
    def dispatch(self, request, *args, **kwargs):
        request.proposition_app = {
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

            kwargs['confirm_tab_suffix'] = ' (%s)' % response['count']
        except RequestException:
            pass
        return super().get_context_data(**kwargs)


class BasePagedView(BaseView):
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

    def dispatch(self, request, *args, **kwargs):
        for view in self.get_previous_views():
            if not issubclass(view, BasePagedFormView) or not view.is_form_enabled(self.valid_form_data):
                continue
            form = view.form_class.unserialise_from_session(request)
            if form.is_valid():
                self.valid_form_data[view.form_class.__name__] = form.cleaned_data
            else:
                return redirect(view.url())
        next_url = request.GET.get('next')
        if is_safe_url(next_url, host=request.get_host()):
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
    def is_form_enabled(cls, valid_form_data):
        return True

    def get_form(self, form_class=None):
        if self.request.method == 'GET':
            form = self.form_class.unserialise_from_session(self.request)
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
        form.serialise_to_session()
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


class PrisonerCheckView(BasePagedView):
    title = _('Confirm prisoner details')
    url_name = 'prisoner_check'
    previous_view = PrisonerView

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

    def get(self, request, *args, **kwargs):
        if request.is_ajax():
            balances = self.get_nomis_balances()
            if balances:
                return JsonResponse({
                    'spends': currency(balances['spends'], '£'),
                    'private': currency(balances['cash'], '£'),
                    'savings': currency(balances['savings'], '£'),
                })
            else:
                raise Http404('Balance not available')
        return super().get(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['nomis_balances'] = self.get_nomis_balances()
        return kwargs


class RecipientContactView(BasePagedFormView):
    title = _('Enter recipient details')
    url_name = 'recipient_contact'
    previous_view = AmountView
    form_class = disbursement_forms.RecipientContactForm

    def get_success_url(self):
        form_data = self.get_valid_form_data(SendingMethodView)
        if form_data['method'] == disbursement_forms.SENDING_METHOD.CHEQUE:
            self.next_view = DetailsCheckView
        else:
            self.next_view = RecipientBankAccountView
        return super().get_success_url()


class RecipientBankAccountView(BasePagedFormView):
    title = _('Enter recipient bank details')
    url_name = 'recipient_bank_account'
    previous_view = RecipientContactView
    form_class = disbursement_forms.RecipientBankAccountForm

    @classmethod
    def is_form_enabled(cls, valid_form_data):
        return (
            valid_form_data[SendingMethodView.form_class.__name__]['method'] ==
            disbursement_forms.SENDING_METHOD.BANK_TRANSFER
        )

    def get_context_data(self, **kwargs):
        kwargs.update(self.get_valid_form_data(RecipientContactView))
        return super().get_context_data(**kwargs)


class DetailsCheckView(BasePagedView):
    title = _('Check payment details')
    url_name = 'details_check'
    previous_view = RecipientBankAccountView

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
        try:
            self.api_session.post('/disbursements/', json=disbursement_data)
        except RequestException:
            logger.exception('Failed to create disbursement')
            return redirect('%s?e=connection' % self.previous_view.url())

        self.clear_disbursement(self.request)

        return self.get(request)


# confirmation flow


class PendingListView(BaseView):
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


class PendingDetailView(BaseView):
    title = _('Check payment details')
    url_name = 'pending_detail'

    error_messages = {
        'connection': _('Payment not confirmed due to technical error, try again soon'),
        'invalid': _(
            'There was a problem with some of the payment details, please '
            'check them again and fix if necessary'
        )
    }

    def get_context_data(self, **kwargs):
        kwargs['breadcrumbs_back'] = PendingListView.url()
        context = super().get_context_data(**kwargs)

        if 'e' in self.request.GET:
            context['errors'] = [self.error_messages.get(self.request.GET['e'])]

        try:
            context['disbursement'] = self.api_session.get(
                'disbursements/{pk}/'.format(pk=kwargs['pk'])
            ).json()
        except HttpNotFoundError:
            raise Http404('Disbursement %s not found' % kwargs['pk'])
        context.update(
            **get_disbursement_viability(self.request, context['disbursement'])
        )

        form = disbursement_forms.RejectDisbursementForm()
        context['reject_form'] = form

        return context

    def get_confirm_url(self):
        return ConfirmPendingView.url(**self.kwargs)

    def get_reject_url(self):
        return RejectPendingView.url(**self.kwargs)


class ConfirmPendingView(BaseView):
    title = _('Payment confirmation')
    url_name = 'pending_confirm'
    http_method_names = ['post']

    def create_nomis_transaction(self, context):
        disbursement = context['disbursement']
        try:
            nomis_response = nomis.create_transaction(
                prison_id=disbursement['prison'],
                prisoner_number=disbursement['prisoner_number'],
                amount=disbursement['amount']*-1,
                record_id='d%s' % disbursement['id'],
                description='Sent to {recipient_first_name} {recipient_last_name}'.format(
                    recipient_first_name=disbursement['recipient_first_name'],
                    recipient_last_name=disbursement['recipient_last_name']
                ),
                transaction_type='RELA',
                retries=1
            )
            context['success'] = True
            context['disbursement']['nomis_transaction_id'] = nomis_response['id']
        except HTTPError as e:
            if e.response.status_code == 409:
                logger.warning(
                    'Disbursement %s was already present in NOMIS' % disbursement['id']
                )
                context['success'] = True
            elif e.response.status_code >= 500:
                logger.error(
                    'Disbursement %s could not be made as NOMIS is unavailable'
                    % disbursement['id']
                )
                context['unavailable'] = True
            else:
                logger.warning('Disbursement %s is invalid' % disbursement['id'])
                context['invalid'] = True
        except RequestException:
            logger.exception(
                'Disbursement %s could not be made as NOMIS is unavailable'
                % disbursement['id']
            )
            context['unavailable'] = True

        return context

    def post(self, _, **kwargs):
        context = self.get_context_data(**kwargs)

        try:
            disbursement = self.api_session.get(
                'disbursements/{pk}/'.format(pk=kwargs['pk'])
            ).json()
            context['disbursement'] = disbursement
        except HttpNotFoundError:
            raise Http404

        try:
            if disbursement['resolution'] != 'preconfirmed':
                self.api_session.post(
                    'disbursements/actions/preconfirm/',
                    json={'disbursement_ids': [disbursement['id']]}
                )

            context = self.create_nomis_transaction(context)
        except HTTPError as e:
            if e.response.status_code == 409:
                context['invalid'] = True
            else:
                raise e

        if context.get('success', False):
            update = {'id': disbursement['id']}
            if 'nomis_transaction_id' in context['disbursement']:
                update['nomis_transaction_id'] = (
                    context['disbursement']['nomis_transaction_id']
                )
            self.api_session.post(
                'disbursements/actions/confirm/',
                json=[update]
            )
            return self.render_to_response(context)
        else:
            self.api_session.post(
                'disbursements/actions/reset/',
                json={'disbursement_ids': [disbursement['id']]}
            )

            if context.get('invalid', False):
                return redirect('%s?e=invalid' % PendingDetailView.url(pk=disbursement['id']))
            else:
                return redirect('%s?e=connection' % PendingDetailView.url(pk=disbursement['id']))


class RejectPendingView(BaseView, FormView):
    url_name = 'pending_reject'
    form_class = disbursement_forms.RejectDisbursementForm
    success_url = reverse_lazy('disbursements:%s' % PendingListView.url_name)
    http_method_names = ['post']

    def form_valid(self, form):
        try:
            form.reject(self.request, self.kwargs['pk'])
            messages.info(self.request, _('Payment request cancelled.'))
        except RequestException:
            logger.exception('Could not reject disbursement')
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
            raise Http404('Disbursement %s not found' % kwargs['pk'])
        for view in list(self.get_previous_views()) + [self.__class__]:
            if not hasattr(view, 'form_class') or not view.is_form_enabled(self.valid_form_data):
                continue
            view.form_class.serialise_data(request.session, self.disbursement)
            form = view.form_class.unserialise_from_session(request)
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
        update = self.get_update_payload(form)
        changed_fields = set()
        for field in update:
            if update[field] != self.disbursement[field]:
                changed_fields.add(field)
        if 'prisoner_number' in changed_fields:
            changed_fields.add('prison')
        if changed_fields:
            self.api_session.patch(
                'disbursements/{pk}/'.format(**self.kwargs),
                json={field: update[field] for field in changed_fields}
            )
        return super().form_valid(form)

    def get_update_payload(self, form):
        return form.get_update_payload()

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
        payload = form.get_update_payload()
        payload.update(account_number='', sort_code='', roll_number='')
        return payload

    def get_success_url(self):
        if self.require_bank_account:
            return UpdateRecipientBankAccountView.url(**self.kwargs)
        return super().get_success_url()


class UpdatePrisonerView(BaseEditFormView, PrisonerView):
    url_name = 'update_prisoner'
    previous_view = UpdateSendingMethodView


class UpdateAmountView(BaseEditFormView, AmountView):
    url_name = 'update_amount'
    previous_view = UpdatePrisonerView


class UpdateRecipientContactView(BaseEditFormView, RecipientContactView):
    url_name = 'update_recipient_contact'
    previous_view = UpdateAmountView


class UpdateRecipientBankAccountView(BaseEditFormView, RecipientBankAccountView):
    url_name = 'update_recipient_bank_account'
    previous_view = UpdateRecipientContactView

    def get_update_payload(self, form):
        payload = form.get_update_payload()
        payload.update(method=disbursement_forms.SENDING_METHOD.BANK_TRANSFER)
        return payload


# misc views


class StartView(BaseView):
    url_name = 'start'
    get_success_url = reverse_lazy('disbursements:%s' % SendingMethodView.url_name)


class PaperFormsView(BaseView):
    url_name = 'paper-forms'


class SearchView(BaseView, FormView):
    url_name = 'search'
    form_class = disbursement_forms.SearchForm

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


class ProcessOverview(BaseView):
    url_name = 'process-overview'


class DisbursementGetHelpView(BaseView, GetHelpView):
    url_name = 'submit_ticket'
    base_template_name = 'disbursements/base.html'
    template_name = 'disbursements/feedback/submit_feedback.html'
    success_url = reverse_lazy('disbursements:feedback_success')


class DisbursementGetHelpSuccessView(BaseView, GetHelpSuccessView):
    url_name = 'feedback_success'
    base_template_name = 'disbursements/base.html'
    template_name = 'disbursements/feedback/success.html'
