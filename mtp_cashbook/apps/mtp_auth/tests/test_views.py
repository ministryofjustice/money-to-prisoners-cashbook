import json
from urllib.parse import urljoin

from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from mtp_common.test_utils import silence_logger
import responses

from cashbook.tests import MTPBaseTestCase, api_url

ZENDESK_BASE_URL = 'https://hellozendeskhere.com'


@override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}})
class UserRequestFormTestCase(MTPBaseTestCase):

    def mock_prison_list(self, rsps):
        rsps.add(
            rsps.GET,
            api_url('/prisons/'),
            json={
                'count': 2,
                'results': [
                    {'nomis_id': 'IXB', 'name': 'Prison 1'},
                    {'nomis_id': 'INP', 'name': 'Prison 2'},
                ]
            }
        )


@override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}})
class MovePrisonTestCase(UserRequestFormTestCase):

    def test_form(self):
        self.login()
        with responses.RequestsMock() as rsps:
            self.mock_prison_list(rsps)
            response = self.client.get(reverse('move-prison'))
        self.assertContains(response, 'prison-clerk')
        self.assertDictEqual(
            response.context['form'].initial,
            {
                'first_name': 'My First Name', 'last_name': 'My Last Name',
                'email': 'my-username@mtp.local', 'username': 'my-username',
            }
        )

    def test_success_response(self):
        self.login()
        with responses.RequestsMock() as rsps:
            self.mock_prison_list(rsps)
            rsps.add(
                rsps.POST,
                api_url('/requests/'),
                json={},
                status=201
            )
            rsps.add(
                rsps.GET,
                api_url('/requests/?username=my-username&role__name=prison-clerk'),
                json={'count': 0},
                status=200
            )
            response = self.client.post(reverse('move-prison'), data={
                'first_name': 'My First Name', 'last_name': 'My Last Name',
                'email': 'my-username@mtp.local', 'username': 'my-username',
                'role': 'prison-clerk', 'prison': 'INP',
                'change-role': 'true',
            }, follow=True)
        self.assertContains(response, 'Your request for access has been sent')

    def test_error_response(self):
        self.login()
        with responses.RequestsMock() as rsps:
            self.mock_prison_list(rsps)
            rsps.add(
                rsps.POST,
                api_url('/requests/'),
                json={'non_field_errors': 'ERROR MSG 1'},
                status=400
            )
            rsps.add(
                rsps.GET,
                api_url('/requests/?username=my-username&role__name=prison-clerk'),
                json={'count': 0},
                status=200
            )
            response = self.client.post(reverse('move-prison'), data={
                'first_name': 'My First Name', 'last_name': 'My Last Name',
                'email': 'my-username@mtp.local', 'username': 'my-username',
                'role': 'prison-clerk', 'prison': 'INP',
                'change-role': 'true',
            }, follow=True)
        self.assertContains(response, 'ERROR MSG 1')


@override_settings(
    ZENDESK_BASE_URL=ZENDESK_BASE_URL,
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}
)
class RequestAccessTestCase(UserRequestFormTestCase):
    maxDiff = None

    def test_success_response_no_previous_request(self):
        with responses.RequestsMock() as rsps:
            self.mock_prison_list(rsps)
            rsps.add(
                rsps.POST,
                api_url('/requests/'),
                json={},
                status=201
            )
            rsps.add(
                rsps.GET,
                api_url('/requests/?username=my-username&role__name=prison-clerk'),
                json={'count': 0},
                status=200
            )
            response = self.client.post(
                reverse('sign-up'),
                data={
                    'first_name': 'My First Name',
                    'last_name': 'My Last Name',
                    'email': 'my-username@mtp.local',
                    'username': 'my-username',
                    'role': 'prison-clerk',
                    'prison': 'INP',
                    'reason': 'because'
                },
                follow=True
            )
        self.assertContains(response, 'Your request for access has been sent')

    def test_success_response_previous_request(self):
        with responses.RequestsMock() as rsps:
            self.mock_prison_list(rsps)
            rsps.add(
                rsps.GET,
                api_url('/requests/?username=my-username&role__name=prison-clerk'),
                json={'count': 1},
                status=200
            )
            zendesk_url = urljoin(
                ZENDESK_BASE_URL,
                'api/v2/tickets.json',
            )
            rsps.add(
                rsps.POST,
                zendesk_url,
                status=200
            )
            response = self.client.post(
                reverse('sign-up'),
                data={
                    'first_name': 'My First Name',
                    'last_name': 'My Last Name',
                    'email': 'my-username@mtp.local',
                    'username': 'my-username',
                    'role': 'prison-clerk',
                    'prison': 'INP',
                    'reason': 'because'
                },
                follow=True
            )
            self.assertContains(response, 'Your request for access has been sent')
            zendesk_request = list(filter(
                lambda c: c.request.method == 'POST' and c.request.url == zendesk_url,
                rsps.calls
            ))
            self.assertEqual(len(zendesk_request), 1)
            zendesk_request_payload = json.loads(zendesk_request[0].request.body)
            self.assertDictEqual(
                zendesk_request_payload,
                {
                    'ticket': {
                        'comment': {
                            'body': (
                                'Requesting a new staff account - Digital Cashbook\n'
                                '=================================================\n'
                                '\n'
                                'Reason for requesting account: because'
                                '\n'
                                '\n'
                                '---\n'
                                '\n'
                                'Forename: My First Name\n'
                                'Surname: My Last Name\n'
                                'Username (Quantum ID): my-username\n'
                                'Staff email: my-username@mtp.local\n'
                                'Prison: Prison 2\n'
                                'Account Type: prison-clerk'
                            )
                        },
                        'custom_fields': [
                            {'id': 26047167, 'value': ''},
                            {'id': 29241738, 'value': 'my-username'}
                        ],
                        'group_id': 26417927,
                        'requester': {
                            'email': 'my-username@mtp.local',
                            'name': 'Sender: my-username'
                        },
                        'subject': 'MTP for digital team - Digital Cashbook - Request for new staff account',
                        'tags': ['feedback', 'mtp', 'cashbook', 'account_request', settings.ENVIRONMENT]
                    }
                }
            )

    def test_error_response(self):
        with responses.RequestsMock() as rsps, silence_logger():
            self.mock_prison_list(rsps)
            rsps.add(
                rsps.GET,
                api_url('/requests/?username=my-username&role__name=prison-clerk'),
                json={'count': 0},
                status=400
            )
            response = self.client.post(
                reverse('sign-up'),
                data={
                    'first_name': 'My First Name',
                    'last_name': 'My Last Name',
                    'email': 'my-username@mtp.local',
                    'username': 'my-username',
                    'role': 'prison-clerk',
                    'prison': 'INP',
                    'reason': 'because'
                },
                follow=True
            )
        self.assertContains(response, 'This service is currently unavailable')
