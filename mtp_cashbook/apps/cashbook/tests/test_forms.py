import datetime
from unittest import mock

from django.conf import settings
from django.test.testcases import SimpleTestCase

from cashbook.forms import ProcessTransactionBatchForm, DiscardLockedTransactionsForm, \
    FilterTransactionHistoryForm


class ProcessTransactionBatchFormTestCase(SimpleTestCase):

    def setUp(self):
        super(ProcessTransactionBatchFormTestCase, self).setUp()
        self.user = mock.MagicMock()
        self.request = mock.MagicMock()

        self.locked_transactions_response = {
            'count': 4,
            'results': [{'id': i} for i in range(1, 5)]
        }

    @mock.patch('cashbook.forms.get_connection')
    def __call__(self, result, mocked_get_connection, *args, **kwargs):
        self.mocked_get_connection = mocked_get_connection
        super(ProcessTransactionBatchFormTestCase, self).__call__(result, *args, **kwargs)

    def test_init_form_with_already_locked_transactions(self):
        self.mocked_get_connection().\
            cashbook.\
            transactions.\
            get.return_value = self.locked_transactions_response

        form = ProcessTransactionBatchForm(self.request)

        expected_choices = [
            (t['id'], t) for t in self.locked_transactions_response['results']
        ]
        self.assertEqual(form.transaction_choices, expected_choices)
        self.assertEqual(form.fields['transactions'].choices, expected_choices)

    def test_init_form_with_no_locked_transactions(self):
        self.mocked_get_connection().\
            cashbook.\
            transactions.get.side_effect = [
                {
                    'count': 0,
                    'results': []
                },
            ] + [self.locked_transactions_response]

        form = ProcessTransactionBatchForm(self.request)
        expected_choices = [
            (t['id'], t) for t in self.locked_transactions_response['results']
        ]
        self.assertEqual(form.transaction_choices, expected_choices)
        self.assertEqual(form.fields['transactions'].choices, expected_choices)

    def test_credit_some(self):
        """
        Tests that [2, 3] gets credited and [1, 4] discarded
        """
        self.mocked_get_connection().\
            cashbook.\
            transactions.\
            get.return_value = self.locked_transactions_response

        to_credit = ['2', '3']
        form = ProcessTransactionBatchForm(
            self.request,
            data={
                'transactions': to_credit
            }
        )
        self.assertTrue(form.is_valid())
        form.save()

        # checking call to patch
        mocked_patch = form.client.cashbook.transactions.patch
        self.assertEqual(mocked_patch.call_count, 1)
        credited_transactions = mocked_patch.call_args[0][0]
        self.assertListEqual(
            sorted([t['id'] for t in credited_transactions]),
            sorted(to_credit)
        )

        # checking call to unlock
        mocked_unlock = form.client.cashbook.transactions.actions.unlock.post
        self.assertEqual(mocked_unlock.call_count, 1)
        discarded_transactions = mocked_unlock.call_args[0][0]
        self.assertListEqual(
            sorted(discarded_transactions['transaction_ids']),
            sorted(['1', '4'])
        )

    def test_credit_all(self):
        """
        Tests that all the transactions get credited.
        """
        self.mocked_get_connection().\
            cashbook.\
            transactions.\
            get.return_value = self.locked_transactions_response

        to_credit = [t['id'] for t in self.locked_transactions_response['results']]
        form = ProcessTransactionBatchForm(
            self.request,
            data={
                'transactions': to_credit
            }
        )
        self.assertTrue(form.is_valid())
        form.save()

        # checking call to patch
        mocked_patch = form.client.cashbook.transactions.patch
        self.assertEqual(mocked_patch.call_count, 1)
        credited_transactions = mocked_patch.call_args[0][0]
        self.assertListEqual(
            sorted([int(t['id']) for t in credited_transactions]),
            sorted(to_credit)
        )

        # checking that no call to unlock has been made
        mocked_unlock = form.client.cashbook.transactions.actions.unlock.post
        self.assertEqual(mocked_unlock.call_count, 0)

    def test_discard_all(self):
        """
        Tests that the form discards all transactions, also the ones
        selected to be credited.
        """
        self.mocked_get_connection().\
            cashbook.\
            transactions.\
            get.return_value = self.locked_transactions_response

        ignored_to_credit = ['2', '3']
        form = ProcessTransactionBatchForm(
            self.request,
            data={
                'transactions': ignored_to_credit,
                'discard': '1'
            }
        )
        self.assertTrue(form.is_valid())
        form.save()

        # checking that no call to patch has been made
        mocked_patch = form.client.cashbook.transactions.patch
        self.assertEqual(mocked_patch.call_count, 0)

        # checking call to unlock with all transactions
        mocked_unlock = form.client.cashbook.transactions.actions.unlock.post
        self.assertEqual(mocked_unlock.call_count, 1)
        discarded_transactions = mocked_unlock.call_args[0][0]
        self.assertListEqual(
            sorted(discarded_transactions['transaction_ids']),
            sorted(
                [str(t['id']) for t in self.locked_transactions_response['results']]
            )
        )


class DiscardLockedTranscationsFormTestCase(SimpleTestCase):

    def setUp(self):
        super(DiscardLockedTranscationsFormTestCase, self).setUp()
        self.user = mock.MagicMock()
        self.request = mock.MagicMock()

        self.locked_transactions_response = {
            'count': 4,
            'results': [
                {
                    'id': i,
                    'owner': 1 if i % 2 else 2,
                    'owner_name': 'Fred' if i % 2 else 'Mary',
                    'prison': 2,
                    'amount': 123,
                    'locked_at': '2015-10-10T12:00:00Z',
                }
                for i in range(1, 5)
            ]
        }

    @mock.patch('cashbook.forms.get_connection')
    def __call__(self, result, mocked_get_connection, *args, **kwargs):
        self.mocked_get_connection = mocked_get_connection
        super(DiscardLockedTranscationsFormTestCase, self).__call__(result, *args, **kwargs)

    def test_discard_some(self):
        """
        Tests that the form discards all transactions, also the ones
        selected to be credited.
        """
        self.mocked_get_connection().\
            cashbook.\
            transactions.\
            locked.\
            get.return_value = self.locked_transactions_response

        expected_to_discard = ['1', '3']
        form_to_discard = ['1 3']

        form = DiscardLockedTransactionsForm(
            self.request,
            data={
                'transactions': form_to_discard
            }
        )
        self.assertTrue(form.is_valid())
        form.save()

        # checking call to unlock
        mocked_unlock = form.client.cashbook.transactions.actions.unlock.post
        self.assertEqual(mocked_unlock.call_count, 1)
        discarded_transactions = mocked_unlock.call_args[0][0]
        self.assertListEqual(
            sorted(discarded_transactions['transaction_ids']),
            expected_to_discard
        )


class FilterTransactionHistoryFormTestCase(SimpleTestCase):
    def setUp(self):
        super().setUp()
        self.user = mock.MagicMock(pk=100)
        self.request = mock.MagicMock(user=self.user)

        self.api_call = self.mocked_get_connection().cashbook.\
            transactions.get
        self.api_call.return_value = {
            'count': 0,
            'results': [],
        }

    @mock.patch('cashbook.forms.get_connection')
    def __call__(self, result, mocked_get_connection):
        self.mocked_get_connection = mocked_get_connection
        super().__call__(result)

    def fill_in_form(self, data):
        return FilterTransactionHistoryForm(self.request, data=data)

    def assertValidForm(self, data, api_called_with):  # noqa
        form = self.fill_in_form(data)
        self.assertTrue(form.is_valid())
        response = form.transaction_choices
        self.assertEqual(response, [])
        api_called_with.update({
            'limit': settings.REQUEST_PAGE_SIZE,
            'offset': 0,
        })
        self.api_call.assert_called_with(**api_called_with)

    def assertInvalidForm(self, data):  # noqa
        form = self.fill_in_form(data)
        self.assertFalse(form.is_valid())

    def test_valid_history_filter_form(self):
        self.assertValidForm({
            'start': '10/10/2015',
            'end': '17/10/2015',
            'search': '',
        }, {
            'received_at_0': datetime.date(2015, 10, 10),
            'received_at_1': datetime.date(2015, 10, 17),
            'search': '',
        })
        self.assertValidForm({
            'start': '2015-10-10',
            'end': '2015-10-17',
            'search': '',
        }, {
            'received_at_0': datetime.date(2015, 10, 10),
            'received_at_1': datetime.date(2015, 10, 17),
            'search': '',
        })
        self.assertValidForm({
            'start': '10/10/2015',
            'end': '17/10/2015',
            'search': 'John',
        }, {
            'received_at_0': datetime.date(2015, 10, 10),
            'received_at_1': datetime.date(2015, 10, 17),
            'search': 'John',
        })

    def test_invalid_history_filter_form(self):
        self.assertInvalidForm({
            'start': '',
            'end': '',
            'owner': '',
            'search': '',
        })
        self.assertInvalidForm({
            'start': '11/10/2015',
            'end': '10/10/2015',
            'owner': '',
            'search': '',
        })
        self.assertInvalidForm({
            'received_at_0': '01/10/2015',
            'received_at_1': '10/10/2015',
            'owner': '',
            'search': '',
        })
