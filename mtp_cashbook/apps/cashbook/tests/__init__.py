import logging
from unittest import mock

from django.core.urlresolvers import reverse
from django.test import SimpleTestCase
from django.test.runner import DiscoverRunner
from django.utils.functional import cached_property

from moj_auth.tests.utils import generate_tokens


class TestRunner(DiscoverRunner):
    def run_suite(self, suite, **kwargs):
        if self.verbosity < 2:
            # makes test output quieter because some tests deliberately cause warning messages
            logger = logging.getLogger('mtp')
            logger.setLevel(logging.ERROR)
        return super(TestRunner, self).run_suite(suite, **kwargs)


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
        user_data = {
            'first_name': 'My First Name',
            'last_name': 'My Last Name',
            'username': credentials['username'],
            'prisons': ['prison1']
        }

        return {
            'credentials': credentials,
            'user_data': user_data,
            'token': token,
            'user_pk': user_pk
        }

    @mock.patch('moj_auth.backends.api_client')
    def login(self, mocked_auth_client, login_data=None):
        if not login_data:
            login_data = self._default_login_data

        mocked_auth_client.authenticate.return_value = {
            'pk': login_data['user_pk'],
            'token': login_data['token'],
            'user_data': login_data['user_data']
        }

        response = self.client.post(
            self.login_url, data=login_data['credentials'], follow=True
        )

        self.assertEqual(response.status_code, 200)

    def logout(self):
        response = self.client.post(self.logout_url, follow=True)
        self.assertEqual(response.status_code, 200)
