import mock

from django.core.urlresolvers import reverse

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
