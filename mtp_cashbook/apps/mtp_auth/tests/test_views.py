import mock

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import SimpleTestCase
from django.utils.encoding import force_text

from mtp_auth import SESSION_KEY, BACKEND_SESSION_KEY, \
    AUTH_TOKEN_SESSION_KEY

from .utils import generate_tokens


@mock.patch('mtp_auth.backends.api_client')
class LoginViewTestCase(SimpleTestCase):
    """
    Tests that the login flow works as expected.
    """

    def setUp(self, *args, **kwargs):
        super(LoginViewTestCase, self).setUp(*args, **kwargs)

        self.credentials = {
            'username': 'my-username',
            'password': 'my-password'
        }
        self.login_url = reverse(u'auth:login')
        self.logout_url = reverse(u'auth:logout')

    def test_success(self, mocked_api_client):
        """
        Successful authentication.
        """
        token = generate_tokens()
        mocked_api_client.authenticate.return_value = token

        # login
        response = self.client.post(
            self.login_url, data=self.credentials, follow=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.client.session[SESSION_KEY],
            self.credentials['username']
        )
        self.assertEqual(
            self.client.session[BACKEND_SESSION_KEY],
            settings.AUTHENTICATION_BACKENDS[0]
        )
        self.assertDictEqual(
            self.client.session[AUTH_TOKEN_SESSION_KEY],
            token
        )

        # logout
        response = self.client.post(self.logout_url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(self.client.session.items()), 0)  # nothing in the session

    def test_invalid_credentials(self, mocked_api_client):
        """
        The User submits invalid credentials.
        """
        # mock the connection, return invalid credentials
        mocked_api_client.authenticate.return_value = None

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
