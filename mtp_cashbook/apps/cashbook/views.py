from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from mtp_cashbook.apps.mtp_auth.api_client import get_connection


class TransactionBatchListView(ListView):

    template_name = 'cashbook/transaction_batch_list.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.client = get_connection(request)
        return super(TransactionBatchListView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user

        resp = self.client.transactions(user.prison)(user.pk).get(status='pending')
        if resp.get('count') == 0:
            resp = self.client.transactions(user.prison)(user.pk).take.post()
        return resp.get('results', [])

    def get_context_data(self, **kwargs):
        context = super(TransactionBatchListView, self).get_context_data(**kwargs)
        context['total'] = sum([x['amount'] for x in context['object_list']])
        return context
