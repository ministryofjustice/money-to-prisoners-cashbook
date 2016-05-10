import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.urlresolvers import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.utils.translation import ngettext
from django.views.generic import FormView, TemplateView
from mtp_common.auth import api_client

from .forms import ProcessCreditBatchForm, DiscardLockedCreditsForm, \
    FilterCreditHistoryForm

logger = logging.getLogger('mtp')


class DashboardView(TemplateView):
    template_name = 'cashbook/dashboard.html'
    discard_batch = False

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.client = api_client.get_connection(request)
        if self.discard_batch:
            form = ProcessCreditBatchForm(request, data={
                'discard': '1'
            })
            if form.is_valid():
                form.save()
        return super(DashboardView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super(DashboardView, self).get_context_data(**kwargs)

        # new credits == available + my locked
        credit_client = self.client.credits
        available = credit_client.get(status='available')
        my_locked = credit_client.get(user=self.request.user.pk, status='locked')
        locked = credit_client.get(status='locked')
        context_data['new_credits'] = available['count'] + my_locked['count']
        context_data['locked_credits'] = locked['count']
        return context_data


class CreditBatchListView(FormView):
    form_class = ProcessCreditBatchForm
    template_name = 'cashbook/credit_batch_list.html'
    success_url = reverse_lazy('dashboard')

    def get_form_kwargs(self):
        form_kwargs = super(CreditBatchListView, self).get_form_kwargs()
        form_kwargs['request'] = self.request
        return form_kwargs

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(CreditBatchListView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreditBatchListView, self).get_context_data(**kwargs)

        credit_choices = context['form'].credit_choices
        context['object_list'] = credit_choices
        context['total'] = sum([x[1]['amount'] for x in credit_choices])
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

        return super(CreditBatchListView, self).form_valid(form)


class CreditsLockedView(FormView):

    form_class = DiscardLockedCreditsForm
    template_name = 'cashbook/credits_locked.html'
    success_url = reverse_lazy('dashboard')

    def get_form_kwargs(self):
        form_kwargs = super(CreditsLockedView, self).get_form_kwargs()
        form_kwargs['request'] = self.request
        return form_kwargs

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(CreditsLockedView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreditsLockedView, self).get_context_data(**kwargs)

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

        return super(CreditsLockedView, self).form_valid(form)


class CreditHistoryView(FormView):
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

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

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
        if page_count > 1:
            page_range = list(range(1, page_count + 1))
        else:
            page_range = []
        previous_page = current_page - 1 if current_page > 1 else None
        next_page = current_page + 1 if page_range and page_range[-1] > current_page else None
        context.update({
            'object_list': object_list,
            'previous_page': previous_page,
            'current_page': current_page,
            'next_page': next_page,
            'page_range': page_range,
            'page_count': page_count,
            'credit_owner_name': self.request.user.get_full_name,
            'DEBIT_CARD_ACTIVE': settings.DEBIT_CARD_ACTIVE
        })
        return context

    def form_valid(self, form):
        return self.render_to_response(self.get_context_data(form=form))
