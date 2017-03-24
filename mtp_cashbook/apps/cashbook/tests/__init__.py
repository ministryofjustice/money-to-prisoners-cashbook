from unittest import mock

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import SimpleTestCase
from django.utils.functional import cached_property
from mtp_common.auth.test_utils import generate_tokens
from mtp_common.auth import urljoin


class MTPBaseTestCase(SimpleTestCase):

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
