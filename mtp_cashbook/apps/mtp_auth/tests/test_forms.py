import mock

from django.test.testcases import SimpleTestCase
from django.utils.encoding import force_text

from mtp_auth.forms import AuthenticationForm


@mock.patch('mtp_auth.forms.authenticate')
class AuthenticationFormTestCase(SimpleTestCase):
    """
    Tests that the AuthenticationForm manages valid/invalid
    credentials and problems with the api.

    Mocks the `authenticate` method so that we can use it
    everywhere in our test methods.
    """

    def setUp(self):
        super(AuthenticationFormTestCase, self).setUp()
        self.credentials = {
            'username': 'testclient',
            'password': 'password',
        }

    def test_invalid_credentials(self, mocked_authenticate):
        """
        The User submits invalid credentials
        """
        mocked_authenticate.return_value = None

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

        mocked_authenticate.assert_called_with(**data)

    def test_success(self, mocked_authenticate):
        """
        Successful authentication.
        """
        mocked_authenticate.return_value = mock.MagicMock()

        form = AuthenticationForm(data=self.credentials)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.non_field_errors(), [])

        mocked_authenticate.assert_called_with(**self.credentials)
