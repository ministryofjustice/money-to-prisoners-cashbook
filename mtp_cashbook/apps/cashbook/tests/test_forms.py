import datetime
from unittest import mock

from django.conf import settings
from django.test.testcases import SimpleTestCase

from cashbook.forms import ProcessCreditBatchForm, DiscardLockedCreditsForm, \
    FilterCreditHistoryForm


class ProcessCreditBatchFormTestCase(SimpleTestCase):

    def setUp(self):
        super(ProcessCreditBatchFormTestCase, self).setUp()
        self.user = mock.MagicMock()
        self.request = mock.MagicMock()

        self.locked_credits_response = {
            'count': 4,
            'results': [
                {
                    'id': i,
                    'amount': 123,
                    'locked_at': '2015-10-10T12:00:00Z',
                    'received_at': '2015-10-09T12:00:00Z'
                }
                for i in range(1, 5)
            ]
        }

    @mock.patch('cashbook.forms.get_connection')
    def __call__(self, result, mocked_get_connection, *args, **kwargs):
        self.mocked_get_connection = mocked_get_connection
        super(ProcessCreditBatchFormTestCase, self).__call__(result, *args, **kwargs)

    def test_init_form_with_already_locked_credits(self):
        self.mocked_get_connection().credits.get.return_value = self.locked_credits_response

        form = ProcessCreditBatchForm(self.request)

        expected_choices = [
            (t['id'], t) for t in self.locked_credits_response['results']
        ]
        self.assertEqual(form.credit_choices, expected_choices)
        self.assertEqual(form.fields['credits'].choices, expected_choices)

    def test_init_form_with_no_locked_credits(self):
        self.mocked_get_connection().credits.get.side_effect = [
                {
                    'count': 0,
                    'results': []
                },
            ] + [self.locked_credits_response]

        form = ProcessCreditBatchForm(self.request)
        expected_choices = [
            (t['id'], t) for t in self.locked_credits_response['results']
        ]
        self.assertEqual(form.credit_choices, expected_choices)
        self.assertEqual(form.fields['credits'].choices, expected_choices)

    def test_credit_some(self):
        """
        Tests that [2, 3] gets credited and [1, 4] discarded
        """
        self.mocked_get_connection().credits.get.return_value = self.locked_credits_response

        to_credit = ['2', '3']
        form = ProcessCreditBatchForm(
            self.request,
            data={
                'credits': to_credit
            }
        )
        self.assertTrue(form.is_valid())
        form.save()

        # checking call to patch
        mocked_patch = form.client.credits.patch
        self.assertEqual(mocked_patch.call_count, 1)
        credited_credits = mocked_patch.call_args[0][0]
        self.assertListEqual(
            sorted([t['id'] for t in credited_credits]),
            sorted(to_credit)
        )

        # checking call to unlock
        mocked_unlock = form.client.credits.actions.unlock.post
        self.assertEqual(mocked_unlock.call_count, 1)
        discarded_credits = mocked_unlock.call_args[0][0]
        self.assertListEqual(
            sorted(discarded_credits['credit_ids']),
            sorted(['1', '4'])
        )

    def test_credit_all(self):
        """
        Tests that all the credits get credited.
        """
        self.mocked_get_connection().credits.get.return_value = self.locked_credits_response

        to_credit = [t['id'] for t in self.locked_credits_response['results']]
        form = ProcessCreditBatchForm(
            self.request,
            data={
                'credits': to_credit
            }
        )
        self.assertTrue(form.is_valid())
        form.save()

        # checking call to patch
        mocked_patch = form.client.credits.patch
        self.assertEqual(mocked_patch.call_count, 1)
        credited_credits = mocked_patch.call_args[0][0]
        self.assertListEqual(
            sorted([int(t['id']) for t in credited_credits]),
            sorted(to_credit)
        )

        # checking that no call to unlock has been made
        mocked_unlock = form.client.credits.actions.unlock.post
        self.assertEqual(mocked_unlock.call_count, 0)

    def test_discard_all(self):
        """
        Tests that the form discards all credits, also the ones
        selected to be credited.
        """
        self.mocked_get_connection().credits.get.return_value = self.locked_credits_response

        ignored_to_credit = ['2', '3']
        form = ProcessCreditBatchForm(
            self.request,
            data={
                'credits': ignored_to_credit,
                'discard': '1'
            }
        )
        self.assertTrue(form.is_valid())
        form.save()

        # checking that no call to patch has been made
        mocked_patch = form.client.credits.patch
        self.assertEqual(mocked_patch.call_count, 0)

        # checking call to unlock with all credits
        mocked_unlock = form.client.credits.actions.unlock.post
        self.assertEqual(mocked_unlock.call_count, 1)
        discarded_credits = mocked_unlock.call_args[0][0]
        self.assertListEqual(
            sorted(discarded_credits['credit_ids']),
            sorted(
                [str(t['id']) for t in self.locked_credits_response['results']]
            )
        )


class DiscardLockedTranscationsFormTestCase(SimpleTestCase):

    def setUp(self):
        super(DiscardLockedTranscationsFormTestCase, self).setUp()
        self.user = mock.MagicMock()
        self.request = mock.MagicMock()

        self.locked_credits_response = {
            'count': 4,
            'results': [
                {
                    'id': i,
                    'owner': 1 if i % 2 else 2,
                    'owner_name': 'Fred' if i % 2 else 'Mary',
                    'prison': 2,
                    'amount': 123,
                    'locked_at': '2015-10-10T12:00:00Z',
                    'received_at': '2015-10-09T12:00:00Z'
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
        Tests that the form discards all credits, also the ones
        selected to be credited.
        """
        self.mocked_get_connection().credits.locked.get.return_value = self.locked_credits_response

        expected_to_discard = ['1', '3']
        form_to_discard = ['1 3']

        form = DiscardLockedCreditsForm(
            self.request,
            data={
                'credits': form_to_discard
            }
        )
        self.assertTrue(form.is_valid())
        form.save()

        # checking call to unlock
        mocked_unlock = form.client.credits.actions.unlock.post
        self.assertEqual(mocked_unlock.call_count, 1)
        discarded_credits = mocked_unlock.call_args[0][0]
        self.assertListEqual(
            sorted(discarded_credits['credit_ids']),
            expected_to_discard
        )


class FilterCreditHistoryFormTestCase(SimpleTestCase):
    def setUp(self):
        super().setUp()
        self.user = mock.MagicMock(pk=100)
        self.request = mock.MagicMock(user=self.user)

        self.api_call = self.mocked_get_connection().credits.get
        self.api_call.return_value = {
            'count': 0,
            'results': [],
        }

    @mock.patch('cashbook.forms.get_connection')
    def __call__(self, result, mocked_get_connection):
        self.mocked_get_connection = mocked_get_connection
        super().__call__(result)

    def fill_in_form(self, data):
        return FilterCreditHistoryForm(self.request, data=data)

    def assertValidForm(self, data, api_called_with):  # noqa
        form = self.fill_in_form(data)
        self.assertTrue(form.is_valid())
        response = form.credit_choices
        self.assertEqual(response, [])
        self.api_call.assert_called_with(**api_called_with)

    def assertInvalidForm(self, data):  # noqa
        form = self.fill_in_form(data)
        self.assertFalse(form.is_valid())

    def test_valid_history_filter_form(self):
        self.assertValidForm({}, {
            'received_at__gte': None,
            'received_at__lt': None,
            'search': '',
            'ordering': '-received_at',
            'page': None,
            'page_size': settings.REQUEST_PAGE_DAYS,
            'page_by_date_field': 'received_at',
        })
        self.assertValidForm({
            'start': '',
            'end': '',
            'search': '',
        }, {
            'received_at__gte': None,
            'received_at__lt': None,
            'search': '',
            'ordering': '-received_at',
            'page': None,
            'page_size': settings.REQUEST_PAGE_DAYS,
            'page_by_date_field': 'received_at',
        })
        self.assertValidForm({
            'start': '10/10/2015',
            'end': '17/10/2015',
            'search': '',
        }, {
            'received_at__gte': datetime.date(2015, 10, 10),
            'received_at__lt': datetime.date(2015, 10, 18),
            'search': '',
            'ordering': '-received_at',
            'page': None,
            'page_size': settings.REQUEST_PAGE_DAYS,
            'page_by_date_field': 'received_at',
        })
        self.assertValidForm({
            'start': '2015-10-10',
            'end': '2015-10-17',
            'search': '',
        }, {
            'received_at__gte': datetime.date(2015, 10, 10),
            'received_at__lt': datetime.date(2015, 10, 18),
            'search': '',
            'ordering': '-received_at',
            'page': None,
            'page_size': settings.REQUEST_PAGE_DAYS,
            'page_by_date_field': 'received_at',
        })
        self.assertValidForm({
            'start': '10/10/2015',
            'end': '17/10/2015',
            'search': 'John',
        }, {
            'received_at__gte': datetime.date(2015, 10, 10),
            'received_at__lt': datetime.date(2015, 10, 18),
            'search': 'John',
            'ordering': '-received_at',
            'page': None,
            'page_size': settings.REQUEST_PAGE_DAYS,
            'page_by_date_field': 'received_at',
        })
        self.assertValidForm({
            'start': '10/10/2015',
            'end': '17/10/2015',
            'search': 'John',
            'page': '1',
        }, {
            'received_at__gte': datetime.date(2015, 10, 10),
            'received_at__lt': datetime.date(2015, 10, 18),
            'search': 'John',
            'ordering': '-received_at',
            'page': 1,
            'page_size': settings.REQUEST_PAGE_DAYS,
            'page_by_date_field': 'received_at',
        })
        self.assertValidForm({
            'start': '10/10/2015',
            'end': '17/10/2015',
            'search': 'John',
            'page': '2',
        }, {
            'received_at__gte': datetime.date(2015, 10, 10),
            'received_at__lt': datetime.date(2015, 10, 18),
            'search': 'John',
            'ordering': '-received_at',
            'page': 2,
            'page_size': settings.REQUEST_PAGE_DAYS,
            'page_by_date_field': 'received_at',
        })

    def test_invalid_history_filter_form(self):
        self.assertInvalidForm({
            'start': '11/10/2015',
            'end': '10/10/2015',
            'search': '',
        })
        self.assertInvalidForm({
            'start': 'today',
            'end': '',
            'search': '',
        })
