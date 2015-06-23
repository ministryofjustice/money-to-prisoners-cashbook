import slumber
from slumber.serialize import Serializer, JsonSerializer
from requests.auth import AuthBase

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils.http import urlencode


class BearerTokenAuth(AuthBase):
    """
    Attaches the Bearer token to the request.
    """
    def __init__(self, token):
        self.token = token

    def get_header(self):
        return ('Authorization', 'Bearer %s' % self.token)

    def __call__(self, request):
        key, token = self.get_header()
        request.headers[key] = token
        return request


class FormSerializer(slumber.serialize.JsonSerializer):
    """
    This FormSerializer has to be used during the authentication
    process as the `django-oauth-toolkit` version that the api app
    is using does not support json format yet (currently in master
    so expected soon).
    """
    key = "form"
    content_types = ["application/x-www-form-urlencoded"]

    def dumps(self, data):
        return urlencode(data)


def get_raw_connection(token=None, serializer='json'):
    """
    Returns a slumber connection configured so that it can be easily
    used to query the API server.

    If you have a token:
        conn = get_raw_connection(token='your-token')
        conn.my_endpoint.get()

    If you want to authenticate as you don't have a token:
        conn = get_raw_connection(serializer='form')
        conn.connection.oauth2.token.post({
            'client_id': 'client-id',
            'client_secret': 'client-secret',
            'grant_type': 'password',
            'username': 'my-username',
            'password': 'my-password'
        })

    If you have a request object and a logged-in user, you might want to use
    this other shortcut function instead:
        get_connection(request).my_endpoint.get()
    """
    auth = BearerTokenAuth(token) if token else None

    s = Serializer(
        default=serializer,
        serializers=[
            FormSerializer(),
            JsonSerializer()
        ]
    )

    return slumber.API(settings.API_URL, serializer=s, auth=auth)


def get_connection(request):
    """
    Returns a slumber connection configured using the token of the
    logged-in user.

    It raises `django.core.exceptions.PermissionDenied` if the user
    is not authenticated.

        response = get_connection(request).my_endpoint.get()
    """
    user = request.user

    if not user:
        raise PermissionDenied(u'no such user')

    return get_raw_connection(user.pk)
