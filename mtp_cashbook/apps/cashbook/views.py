import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.urlresolvers import reverse_lazy, reverse
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _, ngettext
from django.views.generic import FormView, TemplateView
from mtp_common.auth import api_client
from mtp_common import nomis
from requests.exceptions import RequestException

from .utils import expected_nomis_availability, check_pre_approval_required
from .forms import (
    ProcessCreditBatchForm, DiscardLockedCreditsForm, FilterCreditHistoryForm,
    ProcessNewCreditsForm, FilterProcessedCreditsListForm, ProcessManualCreditsForm,
    COMPLETED_INDEX
)

logger = logging.getLogger('mtp')


def inactive_password_change_view(request):
    return render(request, 'cashbook/inactive_password_change.html')


class DashboardView(TemplateView):
    template_name = 'cashbook/dashboard.html'
    discard_batch = False

    @method_decorator(login_required)
    @method_decorator(expected_nomis_availability(False))
    def dispatch(self, request, *args, **kwargs):
        self.client = api_client.get_connection(request)
        if self.discard_batch:
            form = ProcessCreditBatchForm(request, data={
                'discard': '1'
            })
            if form.is_valid():
                form.save()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        # new credits == available + my locked
        credit_client = self.client.credits
        available = credit_client.get(status='available')
        my_locked = credit_client.get(user=self.request.user.pk, status='locked')
        locked = credit_client.get(status='locked')
        all_credits = credit_client.get()

        pre_approval_required = check_pre_approval_required(self.request)
        if pre_approval_required:
            reviewed = credit_client.get(status='available', reviewed=True)
            context_data['reviewed'] = reviewed['count']

        context_data.update({
            'start_page_url': settings.START_PAGE_URL,
            'new_credits': available['count'] + my_locked['count'],
            'locked_credits': locked['count'],
            'all_credits': all_credits['count'],
            'batch_size': my_locked['count'] or min(available['count'], 20),
            'in_progress_users': list({credit['owner_name'] for credit in locked['results']})
        })
        return context_data


class CashbookSubviewMixin(TemplateView):
    title = NotImplemented
    home_url = reverse_lazy('dashboard')

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['breadcrumbs'] = [
            {'name': _('Home'), 'url': self.home_url},
            {'name': self.title}
        ]
        return context_data


@method_decorator(login_required, name='dispatch')
@method_decorator(expected_nomis_availability(False), name='dispatch')
class CreditBatchListView(FormView, CashbookSubviewMixin):
    title = _('New credits to enter')
    form_class = ProcessCreditBatchForm
    template_name = 'cashbook/credit_batch_list.html'
    success_url = reverse_lazy('dashboard')
    home_url = reverse_lazy('dashboard-batch-discard')

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs['request'] = self.request
        return form_kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        credit_choices = context['form'].credit_choices
        context['object_list'] = credit_choices
        context['total'] = sum([x[1]['amount'] for x in credit_choices])
        context['batch_size'] = len(credit_choices)

        credit_client = context['form'].client.credits
        available = credit_client.get(status='available')
        my_locked = credit_client.get(user=self.request.user.pk, status='locked')
        context['new_credits'] = available['count'] + my_locked['count']

        return context

    def form_valid(self, form):
        credited, discarded = form.save()
        credited_count = len(credited)
        discarded_count = len(discarded)

        if credited_count:
            messages.success(
                self.request,
                ngettext(
                    'You’ve added 1 credit to NOMIS.',
                    'You’ve added %(credited)s credits to NOMIS.',
                    credited_count
                ) % {
                    'credited': credited_count
                }
            )

            username = self.request.user.user_data.get('username', 'Unknown')
            logger.info('User "%(username)s" added %(credited)d credits(s) to NOMIS' % {
                'username': username,
                'credited': credited_count,
            }, extra={
                'elk_fields': {
                    '@fields.credited_count': credited_count,
                    '@fields.username': username,
                }
            })

        if discarded_count:
            self.success_url = reverse('dashboard-batch-incomplete')
        else:
            self.success_url = reverse('dashboard-batch-complete')

        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
@method_decorator(expected_nomis_availability(False), name='dispatch')
class CreditsLockedView(FormView, CashbookSubviewMixin):
    title = _('Currently being entered into NOMIS')
    form_class = DiscardLockedCreditsForm
    template_name = 'cashbook/credits_locked.html'
    success_url = reverse_lazy('dashboard')

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs['request'] = self.request
        return form_kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_list'] = context['form'].grouped_credit_choices
        return context

    def form_valid(self, form):
        discarded = form.save()
        discarded_count = len(discarded)

        if discarded_count:
            messages.success(
                self.request,
                ngettext(
                    'You have now returned the credit your '
                    'colleagues were processing to ‘New’ credits.',
                    'You have now returned the %(discarded)s credits your '
                    'colleagues were processing to ‘New’ credits.',
                    discarded_count
                ) % {
                    'discarded': discarded_count
                }
            )

        username = self.request.user.user_data.get('username', 'Unknown')
        logger.info('User "%(username)s" unlocked %(discarded)d credits(s)' % {
            'username': username,
            'discarded': discarded_count,
        }, extra={
            'elk_fields': {
                '@fields.discarded_count': discarded_count,
                '@fields.username': username,
            }
        })

        if discarded_count:
            self.success_url = reverse('dashboard-unlocked-payments')

        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
@method_decorator(expected_nomis_availability(False), name='dispatch')
class CreditHistoryView(FormView, CashbookSubviewMixin):
    title = _('All credits')
    form_class = FilterCreditHistoryForm
    template_name = 'cashbook/credits_history.html'
    success_url = reverse_lazy('credit-history')
    http_method_names = ['get', 'options']

    def get_initial(self):
        initial = super().get_initial()
        initial.update({
            'page': 1,
        })
        return initial

    def get_form_kwargs(self):
        return {
            'request': self.request,
            'data': self.request.GET or {},
            'initial': self.get_initial(),
            'prefix': self.get_prefix(),
        }

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_bound:
            if form.is_valid():
                return self.form_valid(form)
            else:
                return self.form_invalid(form)
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context['form']
        object_list = form.credit_choices
        current_page = form.pagination['page']
        page_count = form.pagination['page_count']
        context.update({
            'object_list': object_list,
            'current_page': current_page,
            'page_count': page_count,
            'credit_owner_name': self.request.user.get_full_name(),
        })
        return context

    def form_valid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


@method_decorator(login_required, name='dispatch')
@method_decorator(expected_nomis_availability(True), name='dispatch')
class ChangeNotificationView(TemplateView):
    template_name = 'cashbook/change_notification.html'


@method_decorator(login_required, name='dispatch')
@method_decorator(expected_nomis_availability(True), name='dispatch')
class NewCreditsView(FormView):
    title = _('New credits')
    form_class = {
        'new': ProcessNewCreditsForm,
        'manual': ProcessManualCreditsForm
    }
    template_name = 'cashbook/new_credits.html'
    success_url = reverse_lazy('new-credits')

    def get_form(self, form_class=None):
        """
        Returns a dict of instances of the forms to be used in this view.
        """
        if form_class is None:
            form_class = self.get_form_class()
        return {
            name: form_class[name](**self.get_form_kwargs())
            for name in form_class
        }

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs['request'] = self.request
        if 'ordering' in self.request.GET:
            form_kwargs['ordering'] = self.request.GET['ordering']
        return form_kwargs

    def get(self, request, *args, **kwargs):
        client = api_client.get_connection(self.request)
        batches = client.credits.batches.get()
        if batches['count']:
            last_batch = batches['results'][0]
            credit_ids = last_batch['credits']
            incomplete_credits = client.credits.get(
                resolution='pending', pk=credit_ids
            )
            if not last_batch['expired'] and incomplete_credits['count']:
                return redirect('processing-credits')

            credited_credits = client.credits.get(
                resolution='credited', pk=credit_ids
            )
            kwargs['credited_credits'] = credited_credits['count']
            kwargs['failed_credits'] = incomplete_credits['count']
            client.credits.batches(last_batch['id']).delete()

        for message in messages.get_messages(request):
            if message.level == COMPLETED_INDEX:
                kwargs['completed_index'] = int(message.message)

        return self.render_to_response(self.get_context_data(**kwargs))

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests, instantiating the relevant form instance with
        the passed POST variables and then checked for validity.
        """
        form_name = None
        for key in request.POST:
            for name in self.get_form_class():
                if key.startswith('submit_%s' % name):
                    form_name = name
        forms = self.get_form()
        if form_name in forms:
            form = forms[form_name]
            if form.is_valid():
                return self.form_valid(form)
        return self.form_invalid(None)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        new_credit_choices = context['form']['new'].credit_choices
        context['new_object_list'] = new_credit_choices
        context['total'] = sum([x[1]['amount'] for x in new_credit_choices])
        context['new_credits'] = len(new_credit_choices)

        manual_credit_choices = context['form']['manual'].credit_choices
        for credit_id, manual_credit in manual_credit_choices:
            try:
                location = nomis.get_location(manual_credit['prisoner_number'])
                manual_credit['new_location'] = location
            except RequestException:
                pass
        context['manual_object_list'] = manual_credit_choices
        context['manual_credits'] = len(manual_credit_choices)

        if context.get('credited_count', 0):
            username = self.request.user.user_data.get('username', 'Unknown')
            logger.info('User "%(username)s" added %(credited)d credits(s) to NOMIS' % {
                'username': username,
                'credited': context['credited_count'],
            }, extra={
                'elk_fields': {
                    '@fields.credited_count': context['credited_count'],
                    '@fields.username': username,
                }
            })

        return context

    def form_valid(self, form):
        credit_choices = form.credit_choices

        credit_id = form.save()

        for i, choice in enumerate(credit_choices):
            if credit_id == choice[0]:
                messages.add_message(self.request, COMPLETED_INDEX, str(i))
        return super().form_valid(form)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data())


@method_decorator(login_required, name='dispatch')
@method_decorator(expected_nomis_availability(True), name='dispatch')
class ProcessingCreditsView(TemplateView):
    title = _('Digital cashbook')
    template_name = 'cashbook/processing_credits.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        client = api_client.get_connection(self.request)
        batches = client.credits.batches.get()
        if batches['count'] == 0 or batches['results'][0]['expired']:
            return redirect('new-credits')
        else:
            credit_ids = batches['results'][0]['credits']
            total = len(credit_ids)
            incomplete_credits = client.credits.get(
                resolution='pending', pk=credit_ids
            )
            done_credit_count = total - incomplete_credits['count']
            context['percentage'] = int((done_credit_count/total)*100)
        return self.render_to_response(context)


@method_decorator(login_required, name='dispatch')
@method_decorator(expected_nomis_availability(True), name='dispatch')
class ProcessedCreditsListView(FormView):
    title = _('Processed credits')
    form_class = FilterProcessedCreditsListForm
    template_name = 'cashbook/processed_credits.html'
    success_url = reverse_lazy('processed-credits-list')

    def get_initial(self):
        initial = super().get_initial()
        initial.update({
            'page': 1,
        })
        return initial

    def get_form_kwargs(self):
        return {
            'request': self.request,
            'data': self.request.GET or {},
            'initial': self.get_initial(),
            'prefix': self.get_prefix(),
        }

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_bound:
            if form.is_valid():
                return self.form_valid(form)
            else:
                return self.form_invalid(form)
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context['form']
        object_list = form.credit_choices
        current_page = form.pagination['page']
        page_count = form.pagination['page_count']
        context.update({
            'object_list': object_list,
            'current_page': current_page,
            'page_count': page_count,
            'credit_owner_name': self.request.user.get_full_name(),
        })
        return context

    def form_valid(self, form):
        return self.render_to_response(self.get_context_data(form=form))
