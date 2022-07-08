import datetime

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


def merge_credit_notice_emails_with_user_prisons(credit_notice_emails, request):
    # only merge when some emails are already set
    if not credit_notice_emails:
        return credit_notice_emails

    credit_notice_emails = {
        credit_notice_email['prison']: credit_notice_email
        for credit_notice_email in credit_notice_emails
    }

    user_prisons = request.user.user_data.get('prisons') or []
    for user_prison in user_prisons:
        if user_prison['nomis_id'] in credit_notice_emails:
            continue
        credit_notice_emails[user_prison['nomis_id']] = {
            'prison': user_prison['nomis_id'],
            'prison_name': user_prison['name'],
            'email': None,
        }

    credit_notice_emails = sorted(
        credit_notice_emails.values(),
        key=lambda credit_notice_email: credit_notice_email['prison_name'],
    )
    return credit_notice_emails


def one_month_ago():
    return datetime.datetime.today() - datetime.timedelta(days=30)
