from mtp_common.auth import USER_DATA_SESSION_KEY
from mtp_common.auth.api_client import get_api_session


def add_user_flag(request, flag):
    api_session = get_api_session(request)
    api_session.put(f'/users/{request.user.username}/flags/{flag}/', json={})
    flags = set(request.user.user_data.get('flags') or [])
    flags.add(flag)
    flags = list(flags)
    request.user.user_data['flags'] = flags
    request.session[USER_DATA_SESSION_KEY] = request.user.user_data


def delete_user_flag(request, flag):
    api_session = get_api_session(request)
    api_session.delete(f'/users/{request.user.username}/flags/{flag}/')
    flags = set(request.user.user_data.get('flags') or [])
    if flag in flags:
        flags.remove(flag)
    flags = list(flags)
    request.user.user_data['flags'] = flags
    request.session[USER_DATA_SESSION_KEY] = request.user.user_data
