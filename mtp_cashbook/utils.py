from mtp_common.auth import USER_DATA_SESSION_KEY
from mtp_common.auth.api_client import get_api_session


def save_user_flags(request, flag):
    api_session = get_api_session(request)
    api_session.put('/users/%s/flags/%s/' % (request.user.username, flag), json={})
    flags = set(request.user.user_data.get('flags') or [])
    flags.add(flag)
    flags = list(flags)
    request.user.user_data['flags'] = flags
    request.session[USER_DATA_SESSION_KEY] = request.user.user_data
