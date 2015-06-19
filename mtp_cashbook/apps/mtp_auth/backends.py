import json
import logging

from requests import ConnectionError as RequestsConnectionError
from slumber.exceptions import HttpClientError

from django.conf import settings

from .api_client import get_auth_connection
from .models import MtpUser
from .exceptions import ConnectionError

logger = logging.getLogger(__name__)


class MtpBackend(object):
    """
    Django authentication backend which authenticates against the api
    server using oauth2.

    Client Id and Secret can be changed in settings.
    """
    def authenticate(self, username=None, password=None):
        """
        Returns a valid `MtpUser` if the authentication is successful
        or None if the credentials were wrong.

        It raises `mtp_auth.exceptions.ConnetionError` in case of
        problems connecting to the api server.
        """
        connection = get_auth_connection()
        try:
            response = connection.oauth2.token.post({
                'client_id': settings.API_CLIENT_ID,
                'client_secret': settings.API_CLIENT_SECRET,
                'grant_type': 'password',
                'username': username,
                'password': password
            })
        except RequestsConnectionError as e:
            logger.error('Cannot connect with the API')
            raise ConnectionError(e)
        except HttpClientError as hcerr:
            error = json.loads(hcerr.content.decode())
            logger.error(error.get('description'))
            return

        user = MtpUser(response['access_token'])
        return user

    def get_user(self, token):
        return MtpUser(token)
