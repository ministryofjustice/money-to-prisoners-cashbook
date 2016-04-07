import logging

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.urlresolvers import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.utils.translation import ungettext
from django.views.generic import FormView, TemplateView

from moj_auth import api_client

from .forms import ProcessTransactionBatchForm, DiscardLockedTransactionsForm, \
    FilterTransactionHistoryForm

logger = logging.getLogger('mtp')


class DashboardView(TemplateView):
    template_name = 'cashbook/dashboard.html'
    discard_batch = False

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.client = api_client.get_connection(request)
        if self.discard_batch:
            form = ProcessTransactionBatchForm(request, data={
                'discard': '1'
            })
            if form.is_valid():
                form.save()
        return super(DashboardView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super(DashboardView, self).get_context_data(**kwargs)

        # new transactions == available + my locked
        transaction_client = self.client.cashbook.transactions
        available = transaction_client.get(status='available')
        my_locked = transaction_client.get(user=self.request.user.pk, status='locked')
        locked = transaction_client.get(status='locked')
        context_data['new_transactions'] = available['count'] + my_locked['count']
        context_data['locked_transactions'] = locked['count']
        return context_data


class TransactionBatchListView(FormView):
    form_class = ProcessTransactionBatchForm
    template_name = 'cashbook/transaction_batch_list.html'
    success_url = reverse_lazy('dashboard')

    def get_form_kwargs(self):
        form_kwargs = super(TransactionBatchListView, self).get_form_kwargs()
        form_kwargs['request'] = self.request
        return form_kwargs

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(TransactionBatchListView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(TransactionBatchListView, self).get_context_data(**kwargs)

        transaction_choices = context['form'].transaction_choices
        context['object_list'] = transaction_choices
        context['total'] = sum([x[1]['amount'] for x in transaction_choices])
        return context

    def form_valid(self, form):
        credited, discarded = form.save()
        credited_count = len(credited)
        discarded_count = len(discarded)

        if credited_count:
            messages.success(
                self.request,
                ungettext(
                    'You’ve credited %(credited)s payment to NOMIS.',
                    'You’ve credited %(credited)s payments to NOMIS.',
                    credited_count
                ) % {
                    'credited': credited_count
                }
            )

            username = self.request.user.user_data.get('username', 'Unknown')
            logger.info('User "%(username)s" credited %(credited)d payment(s) to NOMIS' % {
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

        return super(TransactionBatchListView, self).form_valid(form)


class TransactionsLockedView(FormView):

    form_class = DiscardLockedTransactionsForm
    template_name = 'cashbook/transactions_locked.html'
    success_url = reverse_lazy('dashboard')

    def get_form_kwargs(self):
        form_kwargs = super(TransactionsLockedView, self).get_form_kwargs()
        form_kwargs['request'] = self.request
        return form_kwargs

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(TransactionsLockedView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(TransactionsLockedView, self).get_context_data(**kwargs)

        context['object_list'] = context['form'].grouped_transaction_choices
        return context

    def form_valid(self, form):
        discarded = form.save()
        discarded_count = len(discarded)

        messages.success(
            self.request,
            ungettext(
                'You have now returned the %(discarded)s payment your colleague was processing to ‘New Credits’.',
                'You have now returned the %(discarded)s payments your colleague was processing to ‘New Credits’.',
                discarded_count
            ) % {
                'discarded': discarded_count
            }
        )

        username = self.request.user.user_data.get('username', 'Unknown')
        logger.info('User "%(username)s" unlocked %(discarded)d payment(s)' % {
            'username': username,
            'discarded': discarded_count,
        }, extra={
            'elk_fields': {
                '@fields.discarded_count': discarded_count,
                '@fields.username': username,
            }
        })

        return super(TransactionsLockedView, self).form_valid(form)


class TransactionHistoryView(FormView):
    form_class = FilterTransactionHistoryForm
    template_name = 'cashbook/transactions_history.html'
    success_url = reverse_lazy('transaction-history')
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
        object_list = form.transaction_choices
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
            'transaction_owner_name': self.request.user.get_full_name,
        })
        return context

    def form_valid(self, form):
        return self.render_to_response(self.get_context_data(form=form))
