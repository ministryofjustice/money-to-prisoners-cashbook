import mock
import json
import responses
import datetime

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.test.testcases import SimpleTestCase

from mtp_auth.api_client import REQUEST_TOKEN_URL, authenticate, get_connection

from .utils import generate_tokens


class AuthenticateTestCase(SimpleTestCase):

    @responses.activate
    def test_invalid_credentials(self):
        # mock the response, return 401
        responses.add(
            responses.POST,
            REQUEST_TOKEN_URL,
            status=401,
            content_type='application/json'
        )

        # authenticate, should return None
        token = authenticate(
            'my-username', 'invalid-password'
        )

        self.assertEqual(token, None)

    @responses.activate
    def test_success(self):
        username = 'my-username'

        # mock the response, return token
        expected_token = generate_tokens()
        expected_user_data = {
            'pk': 1,
            'first_name': 'My First Name',
            'last_name': 'My last name',
            'prisons': ['prison1']
        }

        responses.add(
            responses.POST,
            REQUEST_TOKEN_URL,
            body=json.dumps(expected_token),
            status=200,
            content_type='application/json'
        )

        responses.add(
            responses.GET,
            '{base_url}/users/{username}/'.format(
                base_url=settings.API_URL,
                username=username
            ),
            body=json.dumps(expected_user_data),
            status=200,
            content_type='application/json'
        )

        # authenticate, should return authentication data
        data = authenticate(username, 'my-password')

        self.assertEqual(data['pk'], expected_user_data.get('pk'))
        self.assertDictEqual(data['token'], expected_token)
        self.assertDictEqual(data['user_data'], expected_user_data)

    def test_error_if_http_instead_of_https(self):
        """
        Test that if env var OAUTHLIB_INSECURE_TRANSPORT == False
        `authenticate` raises an exception if accessing the api
        using http instead of https.
        """
        from oauthlib.oauth2.rfc6749.errors import InsecureTransportError

        with mock.patch.dict(
            'os.environ', {'OAUTHLIB_INSECURE_TRANSPORT': ''}
        ):
            self.assertRaises(
                InsecureTransportError, authenticate,
                'my-username', 'my-password'
            )


class GetConnectionTestCase(SimpleTestCase):

    def setUp(self):
        """
        Sets up a request mock object with
        request.user.token == generated token.

        It also defines the {base_url}/test/ endpoint which will be
        used by all the test methods.
        """
        super(GetConnectionTestCase, self).setUp()
        self.request = mock.MagicMock(
            user=mock.MagicMock(
                token=generate_tokens()
            )
        )

        self.test_endpoint = '{base_url}/test/'.format(
            base_url=settings.API_URL
        )

    def test_fail_without_logged_in_user(self):
        """
        If request.user is None, the get_connection raises
        PermissionDenied.
        """
        self.request.user = None

        self.assertRaises(
            PermissionDenied, get_connection, self.request
        )

    @responses.activate
    def test_with_valid_access_token(self):
        # mock the response, return valid body
        expected_response = {'success': True}

        responses.add(
            responses.GET,
            self.test_endpoint,
            body=json.dumps(expected_response),
            status=200,
            content_type='application/json'
        )

        # should return the same generated body
        conn = get_connection(self.request)
        result = conn.test.get()

        self.assertDictEqual(result, expected_response)

    @responses.activate
    def test_token_refreshed_automatically(self):
        """
        Test that if I call the /test/ endpoint with an
        expired access token, the module should automatically:

        - request a new access token
        - update request.user.token to the new token
        - finally request /test/ with the new valid token
        """
        def build_expires_at(dt):
            return (
                dt - datetime.datetime(1970, 1, 1)
            ).total_seconds()

        # dates
        now = datetime.datetime.now()
        one_day_delta = datetime.timedelta(days=1)

        expired_yesterday = build_expires_at(now - one_day_delta)
        expires_tomorrow = build_expires_at(now + one_day_delta)

        # set access_token.expires_at to yesterday
        self.request.user.token['expires_at'] = expired_yesterday
        expired_token = self.request.user.token

        # mock the refresh token endpoint, return a new token
        new_token = generate_tokens(expires_at=expires_tomorrow)
        responses.add(
            responses.POST,
            REQUEST_TOKEN_URL,
            body=json.dumps(new_token),
            status=200,
            content_type='application/json'
        )

        # mock the /test/ endpoint, return valid body
        expected_response = {'success': True}
        responses.add(
            responses.GET,
            self.test_endpoint,
            body=json.dumps(expected_response),
            status=200,
            content_type='application/json'
        )

        # test
        conn = get_connection(self.request)
        result = conn.test.get()

        self.assertDictEqual(result, expected_response)
        self.assertDictEqual(self.request.user.token, new_token)
        self.assertNotEqual(
            expired_token['access_token'],
            new_token['access_token']
        )
