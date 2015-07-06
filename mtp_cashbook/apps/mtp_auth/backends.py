from . import api_client
from .models import MtpUser


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
        """
        data = api_client.authenticate(username, password)
        if not data:
            return

        return MtpUser(
            data.get('pk'), data.get('token'), data.get('user_data')
        )

    def get_user(self, pk, token, user_data):
        return MtpUser(pk, token, user_data)
