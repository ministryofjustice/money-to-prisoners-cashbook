import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, TemplateView, View
from mtp_common.api import retrieve_all_pages_for_path
from mtp_common.auth.api_client import get_api_session
from mtp_common.auth.exceptions import HttpNotFoundError
from mtp_common import nomis
from requests.exceptions import HTTPError, RequestException

from disbursements import disbursements_available_required, forms as disbursement_forms
from disbursements.utils import get_disbursement_viability
from feedback.views import GetHelpView, GetHelpSuccessView

logger = logging.getLogger('mtp')


def build_view_url(request, url_name, args=[], kwargs={}):
    url_name = '%s:%s' % (request.resolver_match.namespace, url_name)
    return reverse(url_name, args=args, kwargs=kwargs)


def clear_session_view(request):
    """
    View that clears the session and restarts the user flow.
    @param request: the HTTP request
    """
    DisbursementCompleteView.clear_session(request)
    return redirect(build_view_url(request, DisbursementStartView.url_name))


class DisbursementView(View):

    @cached_property
    def api_session(self):
        return get_api_session(self.request)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        try:
            response = self.api_session.get(
                'disbursements/', params={'resolution': 'pending'}
            ).json()

            context_data['confirm_tab_suffix'] = ' (%s)' % response['count']
        except RequestException:
            pass
        return context_data

    @method_decorator(login_required)
    @method_decorator(disbursements_available_required)
    def dispatch(self, request, *args, **kwargs):
        request.proposition_app = {
            'name': _('Digital disbursements'),
            'url': build_view_url(self.request, DisbursementStartView.url_name),
            'help_url': reverse('disbursements:submit_ticket'),
        }
        return super().dispatch(request, *args, **kwargs)


class DisbursementTemplateView(DisbursementView, TemplateView):
    pass


class CreateDisbursementView(DisbursementView):
    previous_view = None
    final_step = False

    def get_context_data(self, **kwargs):
        if self.previous_view and not self.final_step:
            kwargs['breadcrumbs_back'] = self.get_previous_url()
        return super().get_context_data(**kwargs)

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
        for view in self.get_previous_views(self):
            if not hasattr(view, 'form_class') or not view.is_form_enabled(self.valid_form_data):
                continue
            form = view.form_class.unserialise_from_session(
                request, self.valid_form_data)
            if form.is_valid():
                self.valid_form_data[view.form_name()] = form.cleaned_data
            else:
                redirect_url = getattr(view, 'redirect_url_name', None) or view.url_name
                return redirect(build_view_url(self.request, redirect_url))
        return super().dispatch(request, *args, **kwargs)


class DisbursementGetHelpView(DisbursementView, GetHelpView):
    base_template_name = 'disbursements/base.html'
    template_name = 'disbursements/feedback/submit_feedback.html'
    success_url = reverse_lazy('disbursements:feedback_success')


class DisbursementGetHelpSuccessView(DisbursementView, GetHelpSuccessView):
    base_template_name = 'disbursements/base.html'
    template_name = 'disbursements/feedback/success.html'


class ProcessOverview(TemplateView):
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if request.disbursements_preview:
            request.proposition_app = {
                'name': _('Digital disbursements'),
                'url': reverse('disbursements:process-overview'),
                'help_url': reverse('submit_ticket'),
            }
        elif request.disbursements_available:
            request.proposition_app = {
                'name': _('Digital disbursements'),
                'url': build_view_url(self.request, DisbursementStartView.url_name),
                'help_url': reverse('disbursements:submit_ticket'),
            }
        else:
            return redirect(reverse('home'))
        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self):
        if self.request.disbursements_preview:
            return ['disbursements/process-overview-preview.html']
        return ['disbursements/process-overview.html']


class CreateDisbursementFormView(CreateDisbursementView, FormView):
    @classmethod
    def is_form_enabled(cls, previous_form_data):
        return True

    @classmethod
    def form_name(cls):
        return cls.form_class.__name__

    def get_context_data(self, **kwargs):
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


class DisbursementStartView(CreateDisbursementView, TemplateView):
    url_name = 'start'
    template_name = 'disbursements/start.html'

    def get_success_url(self):
        return build_view_url(self.request, SendingMethodView.url_name)


class SendingMethodView(CreateDisbursementFormView):
    url_name = 'sending_method'
    previous_view = DisbursementStartView
    template_name = 'disbursements/sending-method.html'
    form_class = disbursement_forms.SendingMethodForm

    def get_success_url(self):
        return build_view_url(self.request, PrisonerView.url_name)


class PrisonerView(CreateDisbursementFormView):
    url_name = 'prisoner'
    redirect_url_name = DisbursementStartView.url_name
    previous_view = SendingMethodView
    template_name = 'disbursements/prisoner.html'
    form_class = disbursement_forms.PrisonerForm

    def get_success_url(self):
        return build_view_url(self.request, PrisonerCheckView.url_name)


class PrisonerCheckView(CreateDisbursementView, TemplateView):
    url_name = 'prisoner_check'
    previous_view = PrisonerView
    template_name = 'disbursements/prisoner-check.html'

    def get_context_data(self, **kwargs):
        prisoner_details = self.valid_form_data[PrisonerView.form_name()]
        kwargs.update(**prisoner_details)
        return super().get_context_data(**kwargs)

    def get_success_url(self):
        return build_view_url(self.request, AmountView.url_name)


class AmountView(CreateDisbursementFormView):
    url_name = 'amount'
    previous_view = PrisonerCheckView
    template_name = 'disbursements/amount.html'
    form_class = disbursement_forms.AmountForm

    def get_success_url(self):
        return build_view_url(self.request, RecipientContactView.url_name)


class RecipientContactView(CreateDisbursementFormView):
    url_name = 'recipient_contact'
    previous_view = AmountView
    template_name = 'disbursements/recipient-contact.html'
    form_class = disbursement_forms.RecipientContactForm

    def get_success_url(self):
        sending_method = self.valid_form_data[SendingMethodView.form_name()]
        if sending_method['method'] == disbursement_forms.SENDING_METHOD.CHEQUE:
            return build_view_url(self.request, DetailsCheckView.url_name)
        else:
            return build_view_url(self.request, RecipientBankAccountView.url_name)


class RecipientBankAccountView(CreateDisbursementFormView):
    url_name = 'recipient_bank_account'
    previous_view = RecipientContactView
    template_name = 'disbursements/recipient-bank-account.html'
    form_class = disbursement_forms.RecipientBankAccountForm

    @classmethod
    def is_form_enabled(cls, previous_form_data):
        return (
            previous_form_data[SendingMethodView.form_name()]['method'] ==
            disbursement_forms.SENDING_METHOD.BANK_TRANSFER
        )

    def get_context_data(self, **kwargs):
        recipient_details = self.valid_form_data[RecipientContactView.form_name()]
        kwargs.update(**recipient_details)
        return super().get_context_data(**kwargs)

    def get_success_url(self):
        return build_view_url(self.request, DetailsCheckView.url_name)


class DetailsCheckView(CreateDisbursementView, TemplateView):
    url_name = 'details_check'
    previous_view = RecipientBankAccountView
    template_name = 'disbursements/details-check.html'

    def get_context_data(self, **kwargs):
        prisoner_details = self.valid_form_data[PrisonerView.form_name()]
        recipient_contact_details = self.valid_form_data[RecipientContactView.form_name()]
        sending_method_details = self.valid_form_data[SendingMethodView.form_name()]
        amount_details = self.valid_form_data[AmountView.form_name()]
        recipient_bank_details = self.valid_form_data.get(RecipientBankAccountView.form_name(), {})
        kwargs.update(**prisoner_details)
        kwargs.update(**recipient_contact_details)
        kwargs.update(**recipient_bank_details)
        kwargs.update(**sending_method_details)
        kwargs.update(**amount_details)
        return super().get_context_data(**kwargs)

    def get_success_url(self):
        return build_view_url(self.request, DisbursementHandoverView.url_name)


class DisbursementHandoverView(CreateDisbursementView, TemplateView):
    url_name = 'hand-over'
    previous_view = DetailsCheckView
    template_name = 'disbursements/hand-over.html'
    error_messages = {
        'connection': _('Payment not created due to technical error, try again soon')
    }

    def get_context_data(self, **kwargs):
        if 'e' in self.request.GET:
            kwargs['errors'] = [self.error_messages.get(self.request.GET['e'])]
        return super().get_context_data(**kwargs)

    def get_success_url(self):
        return build_view_url(self.request, DisbursementCompleteView.url_name)


class DisbursementCompleteView(CreateDisbursementView, TemplateView):
    url_name = 'complete'
    previous_view = DisbursementHandoverView
    template_name = 'disbursements/complete.html'
    http_method_names = ['post']
    final_step = True

    def post(self, request, *args, **kwargs):
        prisoner_details = self.valid_form_data[PrisonerView.form_name()]
        recipient_contact_details = self.valid_form_data[RecipientContactView.form_name()]
        sending_method_details = self.valid_form_data[SendingMethodView.form_name()]
        amount_details = self.valid_form_data[AmountView.form_name()]
        recipient_bank_details = self.valid_form_data.get(RecipientBankAccountView.form_name(), {})

        try:
            disbursement_data = {
                'prisoner_number': prisoner_details['prisoner_number'],
                'prison': prisoner_details['prison'],
            }
            disbursement_data.update(**prisoner_details)
            disbursement_data.update(**sending_method_details)
            disbursement_data.update(**amount_details)
            disbursement_data.update(**recipient_contact_details)
            disbursement_data.update(**recipient_bank_details)
            self.api_session.post('/disbursements/', json=disbursement_data)

            response = super().get(request, *args, **kwargs)
            self.clear_session(request)
            return response
        except RequestException:
            logger.exception('Failed to create disbursement')
            return redirect(
                '%s?e=connection' %
                build_view_url(self.request, self.previous_view.url_name)
            )


class SearchView(DisbursementView, FormView):
    url_name = 'search'
    template_name = 'disbursements/search.html'
    form_class = disbursement_forms.SearchForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        request_data = self.get_initial()
        request_data.update(self.request.GET.dict())
        kwargs['data'] = request_data
        return kwargs

    def form_valid(self, form):
        context = self.get_context_data(form=form)
        context['disbursements'] = form.get_object_list()
        return self.render_to_response(context)

    get = FormView.post


class PendingDisbursementListView(DisbursementView, TemplateView):
    title = _('Confirm payments')
    url_name = 'pending_list'
    template_name = 'disbursements/pending-list.html'

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


class PendingDisbursementDetailView(DisbursementView, TemplateView):
    title = _('Check payment details')
    url_name = 'pending_detail'
    template_name = 'disbursements/pending-detail.html'

    error_messages = {
        'connection': _('Payment not confirmed due to technical error, try again soon'),
        'invalid': _(
            'There was a problem with some of the payment details, please '
            'check them again and fix if necessary'
        )
    }

    def get_context_data(self, **kwargs):
        kwargs['breadcrumbs_back'] = build_view_url(self.request, PendingDisbursementListView.url_name)
        context = super().get_context_data(**kwargs)
        self.pk = kwargs['pk']

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
        return build_view_url(
            self.request, PendingDisbursementConfirmView.url_name, args=[self.pk]
        )

    def get_reject_url(self):
        return build_view_url(
            self.request, PendingDisbursementRejectView.url_name, args=[self.pk]
        )


class PendingDisbursementRejectView(View):
    url_name = 'pending_reject'
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        form = disbursement_forms.RejectDisbursementForm(request.POST)
        if form.is_valid():
            form.reject(request, kwargs['pk'])
            messages.info(request, _('Payment request cancelled.'))
        else:
            messages.error(request, _('Unable to cancel payment request.'))
        return redirect(build_view_url(request, PendingDisbursementListView.url_name))


class PendingDisbursementConfirmView(DisbursementView, TemplateView):
    title = _('Payment confirmation')
    url_name = 'pending_confirm'
    template_name = 'disbursements/confirmed.html'
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

    def post(self, request, *args, **kwargs):
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
                return redirect('%s?e=invalid' % build_view_url(
                    request, PendingDisbursementDetailView.url_name,
                    args=[disbursement['id']]
                ))
            else:
                return redirect('%s?e=connection' % build_view_url(
                    request, PendingDisbursementDetailView.url_name,
                    args=[disbursement['id']]
                ))


class UpdateDisbursementFormView(DisbursementView, FormView):
    previous_view = None

    @classmethod
    def clear_session(cls, request):
        for view in [cls, *cls.get_previous_views(cls)]:
            if hasattr(view, 'form_class'):
                view.form_class.delete_from_session(request)

    @classmethod
    def get_previous_views(cls, view):
        if view.previous_view:
            yield from cls.get_previous_views(view.previous_view)
            yield view.previous_view

    @classmethod
    def is_form_enabled(cls, previous_form_data):
        return True

    @classmethod
    def form_name(cls):
        return cls.form_class.__name__

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.valid_form_data = {}

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        if self.request.method == 'GET':
            self.form_class.serialise_data(self.request.session, self.disbursement)
            form = self.form_class.unserialise_from_session(
                self.request, self.valid_form_data)
            context_data['form'] = form
        return context_data

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['previous_form_data'] = self.valid_form_data
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        self.pk = kwargs['pk']

        try:
            self.disbursement = self.api_session.get(
                'disbursements/{pk}/'.format(pk=kwargs['pk'])
            ).json()
        except HttpNotFoundError:
            raise Http404

        for view in self.get_previous_views(self):
            if not hasattr(view, 'form_class') or not view.is_form_enabled(self.valid_form_data):
                continue
            view.form_class.serialise_data(request.session, self.disbursement)
            form = view.form_class.unserialise_from_session(
                request, self.valid_form_data)
            if form.is_valid():
                self.valid_form_data[view.form_name()] = form.cleaned_data
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        update = self.get_update_payload(form)
        changes = {}
        for field in update:
            if update[field] != self.disbursement[field]:
                changes[field] = update[field]
        if changes:
            self.api_session.patch(
                'disbursements/{pk}/'.format(pk=self.pk),
                json=changes
            )
        return super().form_valid(form)

    def get_update_payload(self, form):
        return form.get_update_payload()

    def get_success_url(self):
        self.clear_session(self.request)
        return build_view_url(
            self.request, PendingDisbursementDetailView.url_name, args=[self.pk]
        )


class UpdateSendingMethodView(UpdateDisbursementFormView):
    url_name = 'update_sending_method'
    template_name = 'disbursements/sending-method.html'
    form_class = disbursement_forms.SendingMethodForm

    def form_valid(self, form):
        if form.cleaned_data['method'] == disbursement_forms.SENDING_METHOD.CHEQUE:
            self.require_bank_account = False
            return super().form_valid(form)
        else:
            self.require_bank_account = True
            return super(UpdateDisbursementFormView, self).form_valid(form)

    def get_update_payload(self, form):
        payload = form.get_update_payload()
        payload.update(account_number='', sort_code='', roll_number='')
        return payload

    def get_success_url(self):
        if not self.require_bank_account:
            return super().get_success_url()
        else:
            return build_view_url(
                self.request, UpdateRecipientBankAccountView.url_name, args=[self.pk]
            )


class UpdatePrisonerView(UpdateDisbursementFormView):
    url_name = 'update_prisoner'
    template_name = 'disbursements/prisoner.html'
    form_class = disbursement_forms.PrisonerForm
    previous_view = UpdateSendingMethodView


class UpdateAmountView(UpdateDisbursementFormView):
    url_name = 'update_amount'
    template_name = 'disbursements/amount.html'
    form_class = disbursement_forms.AmountForm
    previous_view = UpdatePrisonerView


class UpdateRecipientContactView(UpdateDisbursementFormView):
    url_name = 'update_recipient_contact'
    template_name = 'disbursements/recipient-contact.html'
    form_class = disbursement_forms.RecipientContactForm
    previous_view = UpdateAmountView


class UpdateRecipientBankAccountView(UpdateDisbursementFormView):
    url_name = 'update_recipient_bank_account'
    template_name = 'disbursements/recipient-bank-account.html'
    form_class = disbursement_forms.RecipientBankAccountForm
    previous_view = UpdateRecipientContactView

    def get_update_payload(self, form):
        payload = form.get_update_payload()
        payload.update(method=disbursement_forms.SENDING_METHOD.BANK_TRANSFER)
        return payload
