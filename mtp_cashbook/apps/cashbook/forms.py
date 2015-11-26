from functools import reduce
from itertools import groupby

from django import forms
from django.utils.dateparse import parse_datetime
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _

from core.utils import retrieve_all_pages
from moj_auth.api_client import get_connection
from .form_fields import MtpTextInput, MtpDateInput, MtpInlineRadioFieldRenderer


class ProcessTransactionBatchForm(forms.Form):
    transactions = forms.MultipleChoiceField(choices=(), required=False)

    def __init__(self, request, *args, **kwargs):
        super(ProcessTransactionBatchForm, self).__init__(*args, **kwargs)
        self.user = request.user
        self.client = get_connection(request)

        self.fields['transactions'].choices = self.transaction_choices

    def _request_locked_transactions(self):
        return retrieve_all_pages(self.client.cashbook.transactions.get,
                                  status='locked', user=self.user.pk)

    def _take_transactions(self):
        self.client.cashbook.transactions.actions.lock.post()

    def clean_transactions(self):
        """
        If discard button clicked => ignore any transactions that might
        have been ticked.
        """
        transactions = self.cleaned_data.get('transactions', [])
        discard = self.data.get('discard') == '1'
        if not transactions and not discard:
            raise forms.ValidationError(_('Only click ‘Done’ when you’ve selected credits processed in NOMIS'))
        if discard:
            transactions = []
        return transactions

    @cached_property
    def transaction_choices(self):
        """
        Gets the transactions currently locked by the user if they exist
        or locks some and returns them if not.
        """
        transactions = self._request_locked_transactions()
        if not self.is_bound and len(transactions) == 0:
            self._take_transactions()
            transactions = self._request_locked_transactions()

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
            self.client.cashbook.transactions.patch(
                [{'id': t_id, 'credited': True} for t_id in to_credit]
            )

        # discard
        if to_discard:
            self.client.cashbook.transactions.actions.unlock.post({
                'transaction_ids': list(to_discard)
            })

        return (to_credit, to_discard)


class DiscardLockedTransactionsForm(forms.Form):
    transactions = forms.MultipleChoiceField(choices=(), required=False)

    def __init__(self, request, *args, **kwargs):
        super(DiscardLockedTransactionsForm, self).__init__(*args, **kwargs)
        self.user = request.user
        self.client = get_connection(request)

        self.fields['transactions'].choices = self.grouped_transaction_choices

    def _request_locked_transactions(self):
        return retrieve_all_pages(self.client.cashbook.transactions.locked.get)

    @cached_property
    def transaction_choices(self):
        """
        Gets the transactions currently locked by all users for prison
        """
        transactions = self._request_locked_transactions()

        return [
            (t['id'], t) for t in transactions
        ]

    @cached_property
    def grouped_transaction_choices(self):
        """
        Gets transactions grouped by prison clerk who currently has them locked
        for current prison
        """
        transactions = self._request_locked_transactions()

        # group by locking prison clerk (needs sort first)
        transactions = sorted(transactions, key=lambda t: '%s%d' % (t['owner_name'], t['owner']))
        grouped_transactions = []
        for owner, group in groupby(transactions, key=lambda t: t['owner']):
            group = list(group)

            locked_ids = ' '.join(sorted(str(t['id']) for t in group))
            grouped_transactions.append((locked_ids, {
                'owner': group[0]['owner'],
                'owner_name': group[0]['owner_name'],
                'owner_prison': group[0]['prison'],
                'locked_count': len(group),
                'locked_amount': sum((t['amount'] for t in group)),
                'locked_at_earliest': parse_datetime(min((t['locked_at'] for t in group))),
            }))
        return grouped_transactions

    def save(self):
        transaction_ids = map(str.split, self.cleaned_data['transactions'])
        transaction_ids = reduce(list.__add__, transaction_ids, [])
        to_discard = set(transaction_ids)

        # discard
        if to_discard:
            self.client.cashbook.transactions.actions.unlock.post({
                'transaction_ids': list(to_discard)
            })

        return to_discard


class FilterTransactionHistoryForm(forms.Form):
    start = forms.DateField(label=_('From received date'),
                            required=True, widget=MtpDateInput)
    end = forms.DateField(label=_('To received date'),
                          required=True, widget=MtpDateInput)
    search = forms.CharField(label=_('Prisoner name, prisoner number or sender name'),
                             required=False, widget=MtpTextInput)

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ''
        self.user = request.user
        self.client = get_connection(request)

    def clean(self):
        start = self.cleaned_data.get('start')
        end = self.cleaned_data.get('end')
        if start and end and start > end:
            self.add_error('end', _('The end date must be after the start date.'))
        return super().clean()

    @cached_property
    def transaction_choices(self):
        filters = {}

        fields = set(self.fields.keys())
        if self.is_valid():
            # valid form
            for field in fields:
                if field in self.cleaned_data:
                    filters[field] = self.cleaned_data[field]
        elif not self.is_bound:
            # no form submission
            for field in fields:
                if field in self.initial:
                    filters[field] = self.initial[field]
        else:
            # invalid form
            return []

        renames = (
            ('start', 'received_at_0'),
            ('end', 'received_at_1'),
        )
        for field_name, api_name in renames:
            if field_name in filters:
                filters[api_name] = filters[field_name]
                del filters[field_name]

        return retrieve_all_pages(self.client.cashbook.transactions.get, **filters)
