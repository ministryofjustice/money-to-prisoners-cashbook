from django.utils.functional import SimpleLazyObject

from . import get_user as auth_get_user


def get_user(request):
    """
    Returns a cached copy of the user if it exists or calls `auth_get_user`
    otherwise.
    """
    if not hasattr(request, '_cached_user'):
        request._cached_user = auth_get_user(request)
    return request._cached_user


class AuthenticationMiddleware(object):
    """
    It simply sets `request.user` so that it can be used in our views.

    The build-in Django one sadly tries to get the user from the database.
    """
    def process_request(self, request):
        request.user = SimpleLazyObject(lambda: get_user(request))
