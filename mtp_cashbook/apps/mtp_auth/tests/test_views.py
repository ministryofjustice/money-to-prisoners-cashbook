from django.test import override_settings
from django.urls import reverse
import responses

from cashbook.tests import MTPBaseTestCase, api_url


@override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}})
class MovePrisonTestCase(MTPBaseTestCase):
    def mock_prison_list(self, rsps):
        rsps.add(rsps.GET, api_url('/prisons/'),
                 json={'count': 2, 'results': [
                     {'nomis_id': 'IXB', 'name': 'Prison 1'},
                     {'nomis_id': 'INP', 'name': 'Prison 2'},
                 ]})

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
