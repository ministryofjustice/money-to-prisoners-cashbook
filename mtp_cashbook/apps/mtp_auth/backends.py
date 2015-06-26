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
        token = api_client.authenticate(username, password)
        if not token:
            return

        return MtpUser(
            username=username,
            token=token
        )

    def get_user(self, username, token):
        return MtpUser(
            username=username,
            token=token
        )
