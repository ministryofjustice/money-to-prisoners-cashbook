import mock

from django.test.testcases import SimpleTestCase
from django.utils.encoding import force_text

from mtp_auth.exceptions import ConnectionError
from mtp_auth.forms import AuthenticationForm


class AuthenticationFormTest(SimpleTestCase):
    """
    Tests that the AuthenticationForm manages valid/invalid
    credentials and problems with the api.
    """

    @mock.patch('mtp_auth.forms.authenticate')
    def __call__(self, result, mocked_authenticate, *args, **kwargs):
        """
        Mocks the `authenticate` method so that we can use it
        everywhere in our test methods.
        """
        self.mocked_authenticate = mocked_authenticate
        super(AuthenticationFormTest, self).__call__(result, *args, **kwargs)

    def setUp(self):
        super(AuthenticationFormTest, self).setUp()
        self.credentials = {
            'username': 'testclient',
            'password': 'password',
        }

    def test_invalid_credentials(self):
        """
        The User submits invalid credentials
        """
        self.mocked_authenticate.return_value = None

        data = {
            'username': 'jsmith_does_not_exist',
            'password': 'test123',
        }

        form = AuthenticationForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.non_field_errors(),
            [force_text(form.error_messages['invalid_login'])]
        )

        self.mocked_authenticate.assert_called_with(**data)

    def test_success(self):
        """
        Successful authentication.
        """
        self.mocked_authenticate.return_value = mock.MagicMock()

        form = AuthenticationForm(data=self.credentials)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.non_field_errors(), [])

        self.mocked_authenticate.assert_called_with(**self.credentials)

    def test_api_connection_error(self):
        """
        The app cannot connect to the api server.
        """
        self.mocked_authenticate.side_effect = ConnectionError()

        form = AuthenticationForm(data=self.credentials)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.non_field_errors(),
            [force_text(form.error_messages['connection_error'])]
        )
