from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.urlresolvers import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView

from .forms import ProcessTransactionBatchForm


class TransactionBatchListView(FormView):

    form_class = ProcessTransactionBatchForm
    template_name = 'cashbook/transaction_batch_list.html'
    success_url = reverse_lazy('index')

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

        messages.success(
            self.request,
            _(
                'Batch processed successfully. \
                %(credited)s credited, %(discarded)s discarded.'
            ) % {
                'credited': len(credited),
                'discarded': len(discarded)
            }
        )
        return super(TransactionBatchListView, self).form_valid(form)
