import mock

from requests import ConnectionError

from django.conf import settings
from django.contrib.auth import SESSION_KEY, BACKEND_SESSION_KEY
from django.core.urlresolvers import reverse
from django.test import SimpleTestCase
from django.utils.encoding import force_text

from slumber.exceptions import HttpClientError


class LoginViewTestCase(SimpleTestCase):
    """
    Tests that the login flow works as expected.
    """

    @mock.patch('mtp_auth.backends.get_auth_connection')
    def __call__(
        self, result,
        mocked_get_auth_connection,
        *args, **kwargs
    ):
        """
        Mocks the connection with the api so that we can control it
        everywhere in our test methods.
        """
        self.mocked_get_auth_connection = mocked_get_auth_connection
        super(LoginViewTestCase, self).__call__(result, *args, **kwargs)

    def setUp(self, *args, **kwargs):
        super(LoginViewTestCase, self).setUp(*args, **kwargs)

        self.credentials = {
            'username': 'my-username',
            'password': 'my-password'
        }
        self.login_url = reverse(u'auth:login')
        self.logout_url = reverse(u'auth:logout')

    def test_success(self):
        """
        Successful authentication.
        """
        # mocking the connection so that it returns a valid access token
        token = '123456789'
        connection = mock.MagicMock()
        connection.oauth2.token.post.return_value = {
            'access_token': token
        }
        self.mocked_get_auth_connection.return_value = connection

        # login
        response = self.client.post(
            self.login_url, data=self.credentials, follow=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session[SESSION_KEY], token)
        self.assertEqual(
            self.client.session[BACKEND_SESSION_KEY],
            settings.AUTHENTICATION_BACKENDS[0]
        )

        # logout
        response = self.client.post(self.logout_url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(self.client.session.items()), 0)  # nothing in the session

    def test_invalid_credentials(self):
        """
        The User submits invalid credentials
        """
        # mocking the connection so that it returns invalid credentials
        self.mocked_get_auth_connection().oauth2.token.post.side_effect = HttpClientError(
            content=b'{"description": "invalid credentials"}'
        )

        response = self.client.post(
            self.login_url, data={
                'username': 'my-username',
                'password': 'wrong-password'
            }, follow=True
        )

        form = response.context_data['form']
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['__all__'],
            [force_text(form.error_messages['invalid_login'])]
        )
        self.assertEqual(len(self.client.session.items()), 0)  # nothing in the session

    def test_api_connection_error(self):
        """
        The app cannot connect to the api server.
        """
        # mocking the connection so that it raises ConnectionError
        self.mocked_get_auth_connection().oauth2.token.post.side_effect = ConnectionError()

        response = self.client.post(
            self.login_url, data=self.credentials, follow=True
        )

        form = response.context_data['form']
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['__all__'],
            [force_text(form.error_messages['connection_error'])]
        )
        self.assertEqual(len(self.client.session.items()), 0)  # nothing in the session
