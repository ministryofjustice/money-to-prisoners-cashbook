from unittest import mock
from urllib.parse import urljoin

from django.conf import settings
from django.test import SimpleTestCase, override_settings
from django.urls import reverse
from django.utils.functional import cached_property
from mtp_common.auth.test_utils import generate_tokens


class MTPBaseTestCase(SimpleTestCase):
    def setUp(self):
        super().setUp()
        self.notifications_mock = mock.patch('mtp_common.templatetags.mtp_common.notifications_for_request',
                                             return_value=[])
        self.notifications_mock.start()

    def tearDown(self):
        self.notifications_mock.stop()
        super().tearDown()

    def assertOnPage(self, response, view_name):  # noqa
        self.assertContains(response, '<!--[%s]-->' % view_name)

    @property
    def login_url(self):
        return reverse('login')

    @property
    def logout_url(self):
        return reverse('logout')

    @cached_property
    def _default_login_data(self):
        user_pk = 100
        credentials = {
            'username': 'my-username',
            'password': 'my-password'
        }
        token = generate_tokens()
        permissions = ['credit.view_credit',
                       'credit.lock_credit', 'credit.unlock_credit',
                       'credit.patch_credited_credit']
        user_data = {
            'first_name': 'My First Name',
            'last_name': 'My Last Name',
            'username': credentials['username'],
            'permissions': permissions,
            'prisons': [{
                'nomis_id': 'BXI',
                'name': 'HMP Brixton',
                'pre_approval_required': False
            }],
        }

        return {
            'user_pk': user_pk,
            'token': token,
            'credentials': credentials,
            'user_data': user_data,
        }

    @mock.patch('mtp_common.auth.backends.api_client')
    def login(self, mocked_auth_client, login_data=None):
        if not login_data:
            login_data = self._default_login_data

        mocked_auth_client.authenticate.return_value = {
            'pk': login_data['user_pk'],
            'token': login_data['token'],
            'user_data': login_data['user_data']
        }

        response = self.client.post(
            self.login_url, data=login_data['credentials'], follow=False
        )

        self.assertEqual(response.status_code, 302)

    def logout(self):
        response = self.client.post(self.logout_url, follow=True)
        self.assertEqual(response.status_code, 200)


def api_url(path):
    return urljoin(settings.API_URL, path)


def nomis_url(path):
    return urljoin(settings.NOMIS_API_BASE_URL, path)


override_nomis_settings = override_settings(
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


def wrap_response_data(*args):
    return {
        'count': len(args),
        'results': args
    }
