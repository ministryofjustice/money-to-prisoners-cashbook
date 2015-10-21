import datetime
import mock

from django.core.urlresolvers import reverse
from django.utils.timezone import now

from core.testing.testcases import MTPBaseTestCase


class DashboardViewTestCase(MTPBaseTestCase):

    @mock.patch('cashbook.views.api_client')
    def __call__(self, result, mocked_api_client, *args, **kwargs):
        self.mocked_api_client = mocked_api_client
        super(DashboardViewTestCase, self).__call__(result, *args, **kwargs)

    @property
    def dashboard_url(self):
        return reverse('dashboard')

    def test_cannot_access_if_not_logged_in(self):
        response = self.client.get(self.dashboard_url)

        redirect_url = '{login_url}?next={dashboard_url}'.format(
            login_url=self.login_url,
            dashboard_url=self.dashboard_url
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, redirect_url)

    def _generate_mock_response(self, available, locked_by_user, overall_locked):
        def mock_response(*args, **kwargs):
            if 'user' in kwargs:
                return {'count': locked_by_user}
            status = kwargs.get('status')
            if status == 'locked':
                return {'count': overall_locked}
            elif status == 'available':
                return {'count': available}
            return None
        return mock_response

    def test_0_available_0_locked_gives_correct_new_count(self):
        self.login()

        conn = self.mocked_api_client.get_connection().cashbook.transactions
        conn.get.side_effect = self._generate_mock_response(0, 0, 0)

        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['new_transactions'], 0)

    def test_some_available_0_locked_gives_correct_new_count(self):
        self.login()

        conn = self.mocked_api_client.get_connection().cashbook.transactions
        conn.get.side_effect = self._generate_mock_response(21, 0, 0)

        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['new_transactions'], 21)

    def test_0_available_some_locked_gives_correct_new_count(self):
        self.login()

        conn = self.mocked_api_client.get_connection().cashbook.transactions
        conn.get.side_effect = self._generate_mock_response(0, 3, 0)

        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['new_transactions'], 3)

    def test_some_available_some_locked_gives_correct_new_count(self):
        self.login()

        conn = self.mocked_api_client.get_connection().cashbook.transactions
        conn.get.side_effect = self._generate_mock_response(21, 3, 0)

        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['new_transactions'], 24)

    def test_locked_transactions_gives_correct_count(self):
        self.login()

        conn = self.mocked_api_client.get_connection().cashbook.transactions
        conn.get.side_effect = self._generate_mock_response(21, 3, 19)

        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['locked_transactions'], 19)


class HistoryViewTestCase(MTPBaseTestCase):
    @mock.patch('cashbook.views.api_client')
    @mock.patch('cashbook.forms.get_connection')
    def __call__(self, result, mocked_get_connection, mocked_api_client):
        self.mocked_api_client = mocked_api_client
        self.mocked_get_connection = mocked_get_connection
        super().__call__(result)

    @property
    def history_url(self):
        return reverse('transaction-history')

    def test_history_view(self):
        self.login()
        login_data = self._default_login_data

        today = now()

        self.mocked_get_connection().cashbook.\
            transactions.get.return_value = {
            'count': 2,
            'results': [
                {
                    'id': 142,
                    'prisoner_name': 'John Smith',
                    'prisoner_number': 'A1234BC',
                    'amount': 5200,
                    'formatted_amount': '£52.00',
                    'sender': 'Fred Smith',
                    'prison': 14,
                    'owner': login_data['user_pk'],
                    'owner_name': '%s %s' % (
                        login_data['user_data']['first_name'],
                        login_data['user_data']['last_name'],
                    ),
                    'received_at': today - datetime.timedelta(days=2),
                    'credited': True,
                    'credited_at': today - datetime.timedelta(days=1),
                    'refunded': False,
                    'refunded_at': None,
                },
                {
                    'id': 183,
                    'prisoner_name': 'John Smith',
                    'prisoner_number': 'A1234BC',
                    'amount': 2650,
                    'formatted_amount': '£26.50',
                    'sender': 'Mary Smith',
                    'prison': 14,
                    'owner': login_data['user_pk'],
                    'owner_name': '%s %s' % (
                        login_data['user_data']['first_name'],
                        login_data['user_data']['last_name'],
                    ),
                    'received_at': today - datetime.timedelta(days=1),
                    'credited': True,
                    'credited_at': today - datetime.timedelta(hours=2),
                    'refunded': False,
                    'refunded_at': None,
                },
            ]
        }

        response = self.client.get(self.history_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 2)
        self.assertEqual(response.context['transaction_owner_name'], '%s %s' % (
            login_data['user_data']['first_name'],
            login_data['user_data']['last_name'],
        ))
        self.assertContains(response, text='Total:', count=2)  # indicates 2 groups of credited transactions
