import datetime
import logging
from unittest import mock

from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.test import override_settings
from django.utils.timezone import now, utc
from mtp_common.auth.exceptions import Forbidden
from mtp_common.test_utils import silence_logger
import responses

from cashbook.tests import MTPBaseTestCase, api_url, nomis_url


class LocaleTestCase(MTPBaseTestCase):
    def test_locale_switches_based_on_browser_language(self):
        languages = (
            ('*', 'en-gb'),
            ('en', 'en-gb'),
            ('en-gb', 'en-gb'),
            ('en-GB, en, *', 'en-gb'),
            ('cy', 'cy'),
            ('cy, en-GB, en, *', 'cy'),
            ('en, cy, *', 'en-gb'),
            ('es', 'en-gb'),
        )
        with silence_logger(name='django.request', level=logging.ERROR):
            for accept_language, expected_slug in languages:
                response = self.client.get('/', HTTP_ACCEPT_LANGUAGE=accept_language)
                self.assertRedirects(response, '/%s/' % expected_slug, fetch_redirect_response=False)
                response = self.client.get('/login/', HTTP_ACCEPT_LANGUAGE=accept_language)
                self.assertRedirects(response, '/%s/login/' % expected_slug, fetch_redirect_response=True)


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

    @mock.patch('mtp_common.auth.backends.api_client')
    def test_cannot_login_with_incorrect_details(self, mock_api_client):
        mock_api_client.authenticate.return_value = None

        response = self.client.post(
            reverse('login'),
            data={'username': 'shall', 'password': 'pass'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())

    @mock.patch('mtp_common.auth.backends.api_client')
    def test_cannot_login_without_app_access(self, mock_api_client):
        mock_api_client.authenticate.side_effect = Forbidden

        response = self.client.post(
            reverse('login'),
            data={'username': 'shall', 'password': 'pass'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())

    def _generate_mock_response(self, available, locked_by_user, overall_locked, all_credits):
        def mock_response(*args, **kwargs):
            if 'user' in kwargs:
                return {'count': locked_by_user}
            status = kwargs.get('status')
            if status == 'locked':
                return {'count': overall_locked, 'results': [{
                    'id': 1,
                    'owner': 1,
                    'owner_name': 'Fred',
                    'prison': 'BXI',
                    'amount': 1123,
                    'locked_at': '2015-10-10T12:00:00Z',
                }]}
            elif status == 'available':
                return {'count': available}
            else:
                return {'count': all_credits}
            return None
        return mock_response

    def test_0_available_0_locked_gives_correct_new_count(self):
        self.login()

        conn = self.mocked_api_client.get_connection().credits
        conn.get.side_effect = self._generate_mock_response(0, 0, 0, 50)

        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['new_credits'], 0)

    def test_some_available_0_locked_gives_correct_new_count(self):
        self.login()

        conn = self.mocked_api_client.get_connection().credits
        conn.get.side_effect = self._generate_mock_response(21, 0, 0, 50)

        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['new_credits'], 21)

    def test_0_available_some_locked_gives_correct_new_count(self):
        self.login()

        conn = self.mocked_api_client.get_connection().credits
        conn.get.side_effect = self._generate_mock_response(0, 3, 0, 50)

        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['new_credits'], 3)

    def test_some_available_some_locked_gives_correct_new_count(self):
        self.login()

        conn = self.mocked_api_client.get_connection().credits
        conn.get.side_effect = self._generate_mock_response(21, 3, 0, 50)

        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['new_credits'], 24)

    def test_locked_credits_gives_correct_count(self):
        self.login()

        conn = self.mocked_api_client.get_connection().credits
        conn.get.side_effect = self._generate_mock_response(21, 3, 19, 50)

        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['locked_credits'], 19)


class LockedViewTestCase(MTPBaseTestCase):
    @mock.patch('cashbook.views.api_client')
    @mock.patch('cashbook.forms.get_connection')
    def __call__(self, result, mocked_get_connection, mocked_api_client):
        self.mocked_api_client = mocked_api_client
        self.mocked_get_connection = mocked_get_connection
        super().__call__(result)

    @property
    def locked_url(self):
        return reverse('credits-locked')

    def test_cannot_access_if_not_logged_in(self):
        response = self.client.get(self.locked_url)

        redirect_url = '{login_url}?next={locked_url}'.format(
            login_url=self.login_url,
            locked_url=self.locked_url
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, redirect_url)

    def test_no_locked_credits(self):
        self.login()
        api_endpoint = self.mocked_get_connection().credits.locked.get
        api_endpoint.return_value = {
            'count': 0,
            'results': []
        }
        response = self.client.get(self.locked_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object_list'], [])

    def test_locked_credits_are_grouped(self):
        api_responses = [
            {
                'count': 3,
                'results': [{
                    'id': 1,
                    'owner': 1,
                    'owner_name': 'Fred',
                    'prison': 'BXI',
                    'amount': 1123,
                    'locked_at': '2015-10-10T12:00:00Z',
                }]
            },
            {
                'count': 3,
                'results': [{
                    'id': 2,
                    'owner': 2,
                    'owner_name': 'Mary',
                    'prison': 'BXI',
                    'amount': 1000,
                    'locked_at': '2015-10-10T13:00:00Z',
                }]
            },
            {
                'count': 3,
                'results': [{
                    'id': 3,
                    'owner': 1,
                    'owner_name': 'Fred',
                    'prison': 'BXI',
                    'amount': 5000,
                    'locked_at': '2015-10-10T14:00:00Z',
                }]
            },
        ]
        expected_groups = [
            ('1 3', {
                'owner': 1,
                'owner_name': 'Fred',
                'owner_prison': 'BXI',
                'locked_count': 2,
                'locked_amount': 6123,
                'locked_at_earliest': utc.localize(datetime.datetime(2015, 10, 10, 12)),
            }),
            ('2', {
                'owner': 2,
                'owner_name': 'Mary',
                'owner_prison': 'BXI',
                'locked_count': 1,
                'locked_amount': 1000,
                'locked_at_earliest': utc.localize(datetime.datetime(2015, 10, 10, 13)),
            })
        ]

        self.login()
        api_endpoint = self.mocked_get_connection().credits.locked.get
        api_endpoint.side_effect = api_responses

        response = self.client.get(self.locked_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object_list'], expected_groups)


class BatchListView(MTPBaseTestCase):
    @mock.patch('cashbook.views.api_client')
    @mock.patch('cashbook.forms.get_connection')
    def __call__(self, result, mocked_get_connection, mocked_api_client):
        self.mocked_api_client = mocked_api_client
        self.mocked_get_connection = mocked_get_connection
        super().__call__(result)

    @property
    def list_url(self):
        return reverse('credit-list')

    @mock.patch('cashbook.views.CreditBatchListView.form_class')
    def test_empty_batch_submitted(self, mocked_form_class):
        mocked_form = mocked_form_class()
        mocked_form.credit_choices = [
            (1, {'id': 1,
                 'amount': 1050,
                 'received_at': datetime.datetime.now()}),
            (2, {'id': 2,
                 'amount': 4500,
                 'received_at': datetime.datetime.now()}),
        ]
        mocked_form.clean_credits.side_effect = ValidationError('empty list and not discarding')
        mocked_form.is_valid.return_value = False

        self.login()
        response = self.client.post(
            self.list_url,
            data={'credits': []},
            follow=False,
        )
        self.assertEqual(response.status_code, 200)

    @mock.patch('cashbook.views.api_client')
    @mock.patch('cashbook.views.CreditBatchListView.form_class')
    def test_incomplete_batch_submitted(self, mocked_form_class, mock_api_client):
        credits_client = mock_api_client.get_connection().credits
        credits_client.get.return_value = {'count': 26}

        mocked_form = mocked_form_class()
        mocked_form.credit_choices = [
            (1, {'id': 1,
                 'amount': 1050,
                 'received_at': datetime.datetime.now()}),
            (2, {'id': 2,
                 'amount': 4500,
                 'received_at': datetime.datetime.now()}),
        ]
        mocked_form.is_valid.return_value = True
        mocked_form.save.return_value = ({1}, {2})

        self.login()
        with silence_logger(name='mtp', level=logging.WARNING):
            response = self.client.post(
                self.list_url,
                data={'credits': [1]},
                follow=False,
            )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, reverse('dashboard-batch-incomplete'), fetch_redirect_response=False
        )

    @mock.patch('cashbook.views.api_client')
    @mock.patch('cashbook.views.CreditBatchListView.form_class')
    def test_complete_batch_submitted(self, mocked_form_class, mock_api_client):
        credits_client = mock_api_client.get_connection().credits
        credits_client.get.return_value = {'count': 26}

        mocked_form = mocked_form_class()
        mocked_form.credit_choices = [
            (1, {'id': 1,
                 'amount': 1050,
                 'received_at': datetime.datetime.now()}),
            (2, {'id': 2,
                 'amount': 4500,
                 'received_at': datetime.datetime.now()}),
        ]
        mocked_form.is_valid.return_value = True
        mocked_form.save.return_value = ({1, 2}, {})

        self.login()
        with silence_logger(name='mtp', level=logging.WARNING):
            response = self.client.post(
                self.list_url,
                data={'credits': [1, 2]},
                follow=False,
            )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, reverse('dashboard-batch-complete'), fetch_redirect_response=False
        )


class HistoryViewTestCase(MTPBaseTestCase):
    @mock.patch('cashbook.views.api_client')
    @mock.patch('cashbook.forms.get_connection')
    def __call__(self, result, mocked_get_connection, mocked_api_client):
        self.mocked_api_client = mocked_api_client
        self.mocked_get_connection = mocked_get_connection
        super().__call__(result)

    @property
    def history_url(self):
        return reverse('credit-history')

    def test_history_view(self):
        self.login()
        login_data = self._default_login_data

        today = now()

        self.mocked_get_connection().credits.get.return_value = {
            'page': 1,
            'page_count': 1,
            'count': 2,
            'results': [
                {
                    'id': 142,
                    'prisoner_name': 'John Smith',
                    'prisoner_number': 'A1234BC',
                    'amount': 5200,
                    'formatted_amount': '£52.00',
                    'sender_name': 'Fred Smith',
                    'prison': 'BXI',
                    'owner': login_data['user_pk'],
                    'owner_name': '%s %s' % (
                        login_data['user_data']['first_name'],
                        login_data['user_data']['last_name'],
                    ),
                    'received_at': today - datetime.timedelta(days=2),
                    'resolution': 'credited',
                    'credited_at': today - datetime.timedelta(days=1),
                    'refunded_at': None,
                },
                {
                    'id': 183,
                    'prisoner_name': 'John Smith',
                    'prisoner_number': 'A1234BC',
                    'amount': 2650,
                    'formatted_amount': '£26.50',
                    'sender_name': 'Mary Smith',
                    'prison': 'BXI',
                    'owner': login_data['user_pk'],
                    'owner_name': '%s %s' % (
                        login_data['user_data']['first_name'],
                        login_data['user_data']['last_name'],
                    ),
                    'received_at': today - datetime.timedelta(days=1),
                    'resolution': 'credited',
                    'credited_at': today - datetime.timedelta(hours=2),
                    'refunded_at': None,
                },
            ]
        }

        response = self.client.get(self.history_url)
        self.assertEqual(response.status_code, 200)
        self.assertSequenceEqual(response.context['page_range'], [1])
        self.assertEqual(response.context['current_page'], 1)
        self.assertEqual(len(response.context['object_list']), 2)
        self.assertEqual(response.context['credit_owner_name'], '%s %s' % (
            login_data['user_data']['first_name'],
            login_data['user_data']['last_name'],
        ))
        self.assertContains(response, text='Total:', count=2)  # indicates 2 groups of credited credits
        self.assertContains(response, text='2 credits received', count=1)

    def test_paged_history_view(self):
        self.login()
        login_data = self._default_login_data

        today = now()

        self.mocked_get_connection().credits.get.return_value = {
            'page': 1,
            'page_count': 2,
            'count': 9,
            'results': [
                {
                    'id': 142 - credit_index,
                    'prisoner_name': 'John Smith',
                    'prisoner_number': 'A1234BC',
                    'amount': 5200,
                    'formatted_amount': '£52.00',
                    'sender_name': 'Fred Smith',
                    'prison': 'BXI',
                    'owner': login_data['user_pk'],
                    'owner_name': '%s %s' % (
                        login_data['user_data']['first_name'],
                        login_data['user_data']['last_name'],
                    ),
                    'received_at': today - datetime.timedelta(days=2),
                    'resolution': 'credited',
                    'credited_at': today - datetime.timedelta(days=1),
                    'refunded_at': None,
                }
                for credit_index in range(5)
            ]
        }

        response = self.client.get(self.history_url)
        self.assertEqual(response.status_code, 200)
        self.assertSequenceEqual(response.context['page_range'], [1, 2])
        self.assertEqual(response.context['current_page'], 1)
        self.assertEqual(len(response.context['object_list']), 5)
        self.assertEqual(response.context['credit_owner_name'], '%s %s' % (
            login_data['user_data']['first_name'],
            login_data['user_data']['last_name'],
        ))
        self.assertContains(response, text='Total:', count=1)  # indicates 1 group of credited credits
        self.assertContains(response, text='9 credits received', count=1)

    def test_many_paged_history_view(self):
        self.login()
        login_data = self._default_login_data

        today = now()

        self.mocked_get_connection().credits.get.return_value = {
            'page': 7,
            'page_count': 27,
            'count': 133,
            'results': [
                {
                    'id': 142 - credit_index,
                    'prisoner_name': 'John Smith',
                    'prisoner_number': 'A1234BC',
                    'amount': 5200,
                    'formatted_amount': '£52.00',
                    'sender_name': 'Fred Smith',
                    'prison': 'BXI',
                    'owner': login_data['user_pk'],
                    'owner_name': '%s %s' % (
                        login_data['user_data']['first_name'],
                        login_data['user_data']['last_name'],
                    ),
                    'received_at': today - datetime.timedelta(days=2),
                    'resolution': 'credited',
                    'credited_at': today - datetime.timedelta(days=1),
                    'refunded_at': None,
                }
                for credit_index in range(5)
            ]
        }

        response = self.client.get(self.history_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_page'], 7)
        self.assertSequenceEqual(response.context['page_range'], [1, 2, 3, None, 5, 6, 7, 8, 9, None, 25, 26, 27])
        self.assertContains(response, text='…', count=2)


override_nomis_settings = override_settings(
    NOMIS_API_AVAILABLE=True,
    NOMIS_API_PRISONS=['BXI'],
    NOMIS_API_BASE_URL='https://nomis.local/',
    NOMIS_API_CLIENT_TOKEN='hello',
    NOMIS_API_PRIVATE_KEY=(
        '-----BEGIN EC PRIVATE KEY-----\n'
        'MHcCAQEEIOhhs3RXk8dU/YQE3j2s6u97mNxAM9s+13S+cF9YVgluoAoGCCqGSM49\n'
        'AwEHoUQDQgAE6l49nl7NN6k6lJBfGPf4QMeHNuER/o+fLlt8mCR5P7LXBfMG6Uj6\n'
        'TUeoge9H2N/cCafyhCKdFRdQF9lYB2jB+A==\n'
        '-----END EC PRIVATE KEY-----\n'
    ),  # this key is just for tests, doesn't do anything
)


class ChangeNotificationTestCase(MTPBaseTestCase):

    @property
    def url(self):
        return reverse('dashboard')

    @override_nomis_settings
    def test_first_visit_with_nomis_available_shows_change_notification(self):
        self.login()
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, reverse('change-notification'))

    @override_nomis_settings
    def test_second_visit_with_nomis_available_skips_change_notification(self):
        self.login()
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, reverse('change-notification'))

        # second visit
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.GET,
                api_url('/credits/'),
                json={
                    'count': 0,
                    'results': []
                },
                status=200,
            )
            response = self.client.get(self.url, follow=True)
            self.assertRedirects(response, reverse('new-credits'))


class NewCreditsViewTestCase(MTPBaseTestCase):

    available_credits = {
        'count': 2,
        'results': [
            {'id': 1,
             'prisoner_name': 'John Smith',
             'prisoner_number': 'A1234BC',
             'prison': 'BXI',
             'amount': 5200,
             'sender_name': 'Fred Smith',
             'received_at': '2017-01-25T12:00:00Z'},
            {'id': 2,
             'prisoner_name': 'John Jones',
             'prisoner_number': 'A1234GG',
             'prison': 'BXI',
             'amount': 4500,
             'sender_name': 'Fred Jones',
             'received_at': '2017-01-25T12:00:00Z'},
        ]
    }

    @property
    def url(self):
        return reverse('new-credits')

    @override_nomis_settings
    def test_new_credits_display(self):
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.GET,
                api_url('/credits/'),
                json=self.available_credits,
                status=200,
            )
            self.login()
            response = self.client.get(self.url, follow=True)
            self.assertContains(response, '52.00')
            self.assertContains(response, '45.00')

    @override_nomis_settings
    def test_new_credits_submit(self):
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.GET,
                api_url('/credits/'),
                json=self.available_credits,
                status=200,
            )
            rsps.add(
                rsps.POST,
                nomis_url('/prison/BXI/offenders/A1234BC/transactions'),
                json={'id': '6244779-1'},
                status=200,
            )
            rsps.add(
                rsps.POST,
                nomis_url('/prison/BXI/offenders/A1234GG/transactions'),
                json={'id': '6244780-1'},
                status=200,
            )
            rsps.add(
                rsps.POST,
                api_url('/credits/actions/credit/'),
                status=204,
            )
            rsps.add(
                rsps.GET,
                api_url('/credits/'),
                json={
                    'count': 0,
                    'results': []
                },
                status=200,
            )

            self.login()
            response = self.client.post(
                self.url,
                data={'credits': [1, 2]},
                follow=True
            )
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, '2 new credits')

    @override_nomis_settings
    def test_new_credits_submit_with_conflict(self):
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.GET,
                api_url('/credits/'),
                json=self.available_credits,
                status=200,
            )
            rsps.add(
                rsps.POST,
                nomis_url('/prison/BXI/offenders/A1234BC/transactions'),
                status=409,
            )
            rsps.add(
                rsps.POST,
                nomis_url('/prison/BXI/offenders/A1234GG/transactions'),
                json={'id': '6244780-1'},
                status=200,
            )
            rsps.add(
                rsps.POST,
                api_url('/credits/actions/credit/'),
                status=204,
            )
            rsps.add(
                rsps.GET,
                api_url('/credits/'),
                json={
                    'count': 0,
                    'results': []
                },
                status=200,
            )

            self.login()
            response = self.client.post(
                self.url,
                data={'credits': [1, 2]},
                follow=True
            )
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, '2 new credits')

    @override_nomis_settings
    def test_new_credits_submit_with_uncreditable(self):
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.GET,
                api_url('/credits/'),
                json=self.available_credits,
                status=200,
            )
            rsps.add(
                rsps.POST,
                nomis_url('/prison/BXI/offenders/A1234BC/transactions'),
                status=400,
            )
            rsps.add(
                rsps.POST,
                nomis_url('/prison/BXI/offenders/A1234GG/transactions'),
                json={'id': '6244780-1'},
                status=200,
            )
            rsps.add(
                rsps.POST,
                api_url('/credits/actions/credit/'),
                status=204,
            )
            rsps.add(
                rsps.GET,
                api_url('/credits/'),
                json={
                    'count': 0,
                    'results': []
                },
                status=200,
            )

            self.login()
            response = self.client.post(
                self.url,
                data={'credits': [1, 2]},
                follow=True
            )
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, '1 new credit')


class AllCreditsViewTestCase(MTPBaseTestCase):

    @property
    def url(self):
        return reverse('all-credits')

    @override_nomis_settings
    def test_history_view(self):
        with responses.RequestsMock() as rsps:
            self.login()
            login_data = self._default_login_data

            rsps.add(
                rsps.GET,
                api_url('/credits/'),
                json={
                    'count': 2,
                    'results': [
                        {
                            'id': 142,
                            'prisoner_name': 'John Smith',
                            'prisoner_number': 'A1234BC',
                            'amount': 5200,
                            'formatted_amount': '£52.00',
                            'sender_name': 'Fred Smith',
                            'prison': 'BXI',
                            'owner': login_data['user_pk'],
                            'owner_name': '%s %s' % (
                                login_data['user_data']['first_name'],
                                login_data['user_data']['last_name'],
                            ),
                            'received_at': '2017-01-25T12:00:00Z',
                            'resolution': 'credited',
                            'credited_at': '2017-01-26T12:00:00Z',
                            'refunded_at': None,
                        },
                        {
                            'id': 183,
                            'prisoner_name': 'John Smith',
                            'prisoner_number': 'A1234BC',
                            'amount': 2650,
                            'formatted_amount': '£26.50',
                            'sender_name': 'Mary Smith',
                            'prison': 'BXI',
                            'owner': login_data['user_pk'],
                            'owner_name': '%s %s' % (
                                login_data['user_data']['first_name'],
                                login_data['user_data']['last_name'],
                            ),
                            'received_at': '2017-01-25T12:00:00Z',
                            'resolution': 'credited',
                            'credited_at': '2017-01-26T12:00:00Z',
                            'refunded_at': None,
                        },
                    ]
                },
                status=200,
            )

            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)
            self.assertSequenceEqual(response.context['page_range'], [1])
            self.assertEqual(response.context['current_page'], 1)
            self.assertEqual(response.context['credit_owner_name'], '%s %s' % (
                login_data['user_data']['first_name'],
                login_data['user_data']['last_name'],
            ))
            self.assertContains(response, text='2 credits received', count=1)
            self.assertContains(response, text='John Smith', count=2)
