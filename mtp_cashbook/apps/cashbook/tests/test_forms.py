import mock

from django.test.testcases import SimpleTestCase

from cashbook.forms import ProcessTransactionBatchForm


class ProcessTransactionBatchFormTestCase(SimpleTestCase):

    def setUp(self):
        super(ProcessTransactionBatchFormTestCase, self).setUp()
        self.user = mock.MagicMock()
        self.request = mock.MagicMock()

        self.pending_transactions_response = {
            'count': 4,
            'results': [{'id': i} for i in range(1, 5)]
        }

    @mock.patch('cashbook.forms.get_connection')
    def __call__(self, result, mocked_get_connection, *args, **kwargs):
        self.mocked_get_connection = mocked_get_connection
        super(ProcessTransactionBatchFormTestCase, self).__call__(result, *args, **kwargs)

    def test_init_form_with_already_locked_transactions(self):
        self.mocked_get_connection().\
            transactions()().\
            get.return_value = self.pending_transactions_response

        form = ProcessTransactionBatchForm(self.request)

        expected_choices = [
            (t['id'], t) for t in self.pending_transactions_response['results']
        ]
        self.assertEqual(form.transaction_choices, expected_choices)
        self.assertEqual(form.fields['transactions'].choices, expected_choices)

    def test_init_form_with_no_locked_transactions(self):
        self.mocked_get_connection().transactions()().get.side_effect = [
            {
                'count': 0,
                'results': 0
            },
        ] + [self.pending_transactions_response]

        form = ProcessTransactionBatchForm(self.request)
        expected_choices = [
            (t['id'], t) for t in self.pending_transactions_response['results']
        ]
        self.assertEqual(form.transaction_choices, expected_choices)
        self.assertEqual(form.fields['transactions'].choices, expected_choices)

    def test_credit_some(self):
        """
        Tests that [2, 3] gets credited and [1, 4] discarded
        """
        self.mocked_get_connection().\
            transactions()().\
            get.return_value = self.pending_transactions_response

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
        mocked_patch = form.client.transactions()().patch
        self.assertEqual(mocked_patch.call_count, 1)
        credited_transactions = mocked_patch.call_args[0][0]
        self.assertListEqual(
            sorted([t['id'] for t in credited_transactions]),
            sorted(to_credit)
        )

        # checking call to release
        mocked_release = form.client.transactions()().release.post
        self.assertEqual(mocked_release.call_count, 1)
        discarded_transactions = mocked_release.call_args[0][0]
        self.assertListEqual(
            sorted(discarded_transactions['transaction_ids']),
            sorted(['1', '4'])
        )

    def test_credit_all(self):
        """
        Tests that all the transactions get credited.
        """
        self.mocked_get_connection().\
            transactions()().\
            get.return_value = self.pending_transactions_response

        to_credit = [t['id'] for t in self.pending_transactions_response['results']]
        form = ProcessTransactionBatchForm(
            self.request,
            data={
                'transactions': to_credit
            }
        )
        self.assertTrue(form.is_valid())
        form.save()

        # checking call to patch
        mocked_patch = form.client.transactions()().patch
        self.assertEqual(mocked_patch.call_count, 1)
        credited_transactions = mocked_patch.call_args[0][0]
        self.assertListEqual(
            sorted([int(t['id']) for t in credited_transactions]),
            sorted(to_credit)
        )

        # checking that no call to release has been made
        mocked_release = form.client.transactions()().release.post
        self.assertEqual(mocked_release.call_count, 0)

    def test_discard_all(self):
        """
        Tests that the form discards all transactions, also the ones
        selected to be credited.
        """
        self.mocked_get_connection().\
            transactions()().\
            get.return_value = self.pending_transactions_response

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
        mocked_patch = form.client.transactions()().patch
        self.assertEqual(mocked_patch.call_count, 0)

        # checking call to release with all transactions
        mocked_release = form.client.transactions()().release.post
        self.assertEqual(mocked_release.call_count, 1)
        discarded_transactions = mocked_release.call_args[0][0]
        self.assertListEqual(
            sorted(discarded_transactions['transaction_ids']),
            sorted(
                [str(t['id']) for t in self.pending_transactions_response['results']]
            )
        )
