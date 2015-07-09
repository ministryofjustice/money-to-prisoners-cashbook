from django import forms
from django.utils.functional import cached_property

from mtp_cashbook.apps.mtp_auth.api_client import get_connection


class ProcessTransactionBatchForm(forms.Form):
    transactions = forms.MultipleChoiceField(choices=(), required=False)

    def __init__(self, request, *args, **kwargs):
        super(ProcessTransactionBatchForm, self).__init__(*args, **kwargs)
        self.user = request.user
        self.client = get_connection(request)

        self.fields['transactions'].choices = self.transaction_choices

    def _request_pending_transactions(self):
        return self.client.transactions(self.user.prison)(self.user.pk).get(status='pending')

    def _take_transactions(self):
        self.client.transactions(self.user.prison)(self.user.pk).take.post()

    def clean_transactions(self):
        """
        If discard button clicked => ignore any transactions that might
        have been ticked.
        """
        transactions = self.cleaned_data.get('transactions', [])
        if self.data.get('discard') == '1':
            transactions = []
        return transactions

    @cached_property
    def transaction_choices(self):
        """
        Gets the transactions currently locked by the user if they exist
        or locks some and returns them if not.
        """
        resp = self._request_pending_transactions()
        if resp.get('count') == 0:
            self._take_transactions()
            resp = self._request_pending_transactions()
        transactions = resp.get('results', [])

        return [
           (t['id'], t) for t in transactions
        ]

    def save(self):
        all_ids = {str(t[0]) for t in self.transaction_choices}
        to_credit = set(self.cleaned_data['transactions'])
        to_discard = all_ids - to_credit

        # The two calls to the api might return a status code != 2xx
        # but we are allowing them to raise an exception here.
        # This shouldn't really happen but if it does often enough,
        # we might want to add some exception handling.

        # credit
        if to_credit:
            self.client.transactions(self.user.prison)(self.user.pk).patch(
                [{'id': t_id, 'credited': True} for t_id in to_credit]
            )

        # discard
        if to_discard:
            self.client.transactions(self.user.prison)(self.user.pk).release.post({
                'transaction_ids': list(to_discard)
            })

        return (to_credit, to_discard)
