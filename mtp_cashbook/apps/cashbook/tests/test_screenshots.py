from contextlib import contextmanager
from datetime import datetime, timedelta
from itertools import cycle, islice, repeat
from unittest import mock

from django.test.testcases import LiveServerThread
from django.test.utils import override_settings
from mtp_common.screenshots import ScreenshotGenerator


def dashboard_stats(**kwargs):
    if kwargs.get('status') == 'available':
        return {'count': 26}
    if kwargs.get('status') == 'locked' and kwargs.get('user') == 1:
        return {'count': 0}
    if kwargs.get('status') == 'locked':
        return {'count': 20}
    else:
        return {'count': 234}


@contextmanager
def prepare():
    with mock.patch('mtp_common.auth.api_client.authenticate') as mock_authenticate, \
            mock.patch('cashbook.views.api_client') as mock_client, \
            override_settings(ENVIRONMENT='prod'):
        user_pk = 1
        token = '???????????????'
        user_data = {
            'first_name': 'John',
            'last_name': 'Smith',
            'username': 'jsmith',
        }
        mock_authenticate.return_value = {
            'pk': user_pk,
            'token': token,
            'user_data': user_data
        }
        credits_client = mock_client.get_connection().credits
        credits_client.get.side_effect = dashboard_stats
        yield mock_client


class CashbookScreenshotGenerator(ScreenshotGenerator):
    def login(self, *args, **kwargs):
        kwargs.setdefault('url', self.live_server_url + '/en-gb/')
        super().login(*args, **kwargs)


class DashboardScreenshotGenerator(CashbookScreenshotGenerator):
    save_as = 'training--intro'

    class MockedServerThread(LiveServerThread):
        def run(self):
            with prepare():
                super().run()

    thread_class = MockedServerThread

    def test_setup_screenshot(self):
        self.login('username', 'password')


class NewCreditsScreenshotGenerator(CashbookScreenshotGenerator):
    save_as = 'training--new-a'

    class MockedServerThread(LiveServerThread):
        def run(self):
            with prepare(), \
                    mock.patch('cashbook.forms.get_connection') as mock_get_connection:
                credits_client = mock_get_connection().credits
                credits_client.get.side_effect = self.credits
                super().run()

        def credits(self, **kwargs):
            if 'offset' not in kwargs:
                return dashboard_stats(**kwargs)
            return {
                'count': 20,
                'results': list(islice(cycle([
                    {
                        'id': 1,
                        'prisoner_number': 'A1409AE',
                        'prisoner_name': 'James Halls',
                        'amount': 4000,
                        'sender_name': 'Wade A'
                    },
                    {
                        'id': 2,
                        'prisoner_number': 'A3142AZ',
                        'prisoner_name': 'Mark Smith',
                        'amount': 2500,
                        'sender_name': 'Campbell V'
                    },
                    {
                        'id': 3,
                        'prisoner_number': 'A2231YK',
                        'prisoner_name': 'Stanley Ward',
                        'amount': 4000,
                        'sender_name': 'James R'
                    },
                    {
                        'id': 4,
                        'prisoner_number': 'A4940OG',
                        'prisoner_name': 'Bradley Dale',
                        'amount': 2500,
                        'sender_name': 'Glen West'
                    },
                    {
                        'id': 5,
                        'prisoner_number': 'A7829IW',
                        'prisoner_name': 'Douglas Jarvis',
                        'amount': 6500,
                        'sender_name': 'James R'
                    },
                    {
                        'id': 6,
                        'prisoner_number': 'A8140GN',
                        'prisoner_name': 'Roge Hopkins',
                        'amount': 5500,
                        'sender_name': 'Joe Bishop'
                    },
                ]), 20))
            }

    thread_class = MockedServerThread

    def test_setup_screenshot(self):
        self.login('username', 'password')
        self.click_on_text('Enter next 20')


class NewCreditsTickedScreenshotGenerator(CashbookScreenshotGenerator):
    save_as = 'training--new-d'
    thread_class = NewCreditsScreenshotGenerator.MockedServerThread

    def test_setup_screenshot(self):
        self.login('username', 'password')
        self.click_on_text('Enter next 20')
        xpath = '//input[@type="checkbox" and @data-amount][1]'
        checkbox_id = self.get_element(xpath).get_attribute('id')
        self.get_element('//label[@for="%s"]' % checkbox_id).click()
        self.set_screenshot_size(top=1150)


class InProgressScreenshotGenerator(CashbookScreenshotGenerator):
    save_as = 'training--in-progress'

    class MockedServerThread(LiveServerThread):
        def run(self):
            with prepare(), \
                    mock.patch('cashbook.forms.get_connection') as mock_get_connection:
                locked_credits_client = mock_get_connection().credits.locked
                locked_date = datetime.now() - timedelta(hours=3)
                locked_credits_client.get.return_value = {
                    'count': 12,
                    'results': repeat({
                        'id': 1,
                        'amount': 4000,
                        'owner': 1,
                        'owner_name': 'Mary Stephenson',
                        'prison': 2,
                        'locked_at': locked_date.strftime('%Y-%m-%dT%H:%M:%SZ')
                    }, 12)
                }
                super().run()

    thread_class = MockedServerThread

    def test_setup_screenshot(self):
        self.login('username', 'password')
        self.click_on_text('View')
        self.set_screenshot_size(top=330, left=40)


class HistorySearchScreenshotGenerator(CashbookScreenshotGenerator):
    save_as = 'training--history-a'

    class MockedServerThread(LiveServerThread):
        def run(self):
            with prepare(), \
                    mock.patch('cashbook.forms.get_connection') as mock_get_connection:
                credits_client = mock_get_connection().credits
                credits_client.get.return_value = {'count': 0}
                super().run()

    thread_class = MockedServerThread

    def test_setup_screenshot(self):
        self.login('username', 'password')
        self.click_on_text('View all credits')
        self.type_in('id_search', 'A1409AE')
        self.type_in('id_start', datetime.now().strftime('%d/%m/%y'))


class HistoryResultsScreenshotGenerator(CashbookScreenshotGenerator):
    save_as = 'training--history-b'

    class MockedServerThread(LiveServerThread):
        def run(self):
            with prepare(), \
                    mock.patch('cashbook.forms.get_connection') as mock_get_connection:
                received_at = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
                credits_client = mock_get_connection().credits
                credits_client.get.return_value = {'count': 7, 'results': [
                    {
                        'id': 1,
                        'prisoner_number': 'A1409AE',
                        'prisoner_name': 'James Halls',
                        'amount': 4000,
                        'sender_name': 'Wade A',
                        'received_at': received_at,
                        'credited_at': None,
                        'refunded_at': None,
                        'resolution': 'pending',
                        'anonymous': False,
                        'owner_name': 'Melanie Smith',
                    },
                    {
                        'id': 2,
                        'prisoner_number': 'A3142AZ',
                        'prisoner_name': 'Mark Smith',
                        'amount': 2500,
                        'sender_name': 'Campbell V',
                        'received_at': received_at,
                        'credited_at': None,
                        'refunded_at': None,
                        'resolution': 'pending',
                        'anonymous': False,
                    },
                    {
                        'id': 3,
                        'prisoner_number': 'A2231YK',
                        'prisoner_name': 'Stanley Ward',
                        'amount': 4000,
                        'sender_name': 'James R',
                        'received_at': received_at,
                        'credited_at': None,
                        'refunded_at': None,
                        'resolution': 'pending',
                        'anonymous': False,
                    },
                    {
                        'id': 4,
                        'prisoner_number': 'A4940OG',
                        'prisoner_name': 'Bradley Dale',
                        'amount': 2500,
                        'sender_name': 'Glen West',
                        'received_at': received_at,
                        'credited_at': None,
                        'refunded_at': None,
                        'resolution': 'pending',
                        'anonymous': False,
                        'owner_name': 'Melanie Smith',
                    },
                    {
                        'id': 5,
                        'prisoner_number': 'A7829IW',
                        'prisoner_name': 'Douglas Jarvis',
                        'amount': 1500,
                        'sender_name': 'James R',
                        'received_at': received_at,
                        'credited_at': None,
                        'refunded_at': None,
                        'resolution': 'pending',
                        'anonymous': False,
                    },
                    {
                        'id': 6,
                        'prisoner_number': 'A8140GN',
                        'prisoner_name': 'Roge Hopkins',
                        'amount': 500,
                        'sender_name': None,
                        'received_at': received_at,
                        'credited_at': None,
                        'refunded_at': None,
                        'resolution': 'pending',
                        'anonymous': True,
                    },
                    {
                        'id': 7,
                        'prisoner_number': 'A5729BC',
                        'prisoner_name': 'Josephine Donald',
                        'amount': 500,
                        'sender_name': 'Sian Ball',
                        'received_at': received_at,
                        'credited_at': received_at,
                        'refunded_at': None,
                        'resolution': 'credited',
                        'anonymous': False,
                        'owner_name': 'Melanie Smith',
                    },
                ]}
                super().run()

    thread_class = MockedServerThread

    def test_setup_screenshot(self):
        self.login('username', 'password')
        self.click_on_text('View all credits')
        self.driver.find_elements_by_xpath('//*[text() = "Collapse"]')[1].click()
        self.set_screenshot_size(top=1130)
