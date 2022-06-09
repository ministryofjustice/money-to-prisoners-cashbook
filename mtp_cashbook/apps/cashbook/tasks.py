import logging
from threading import local
from urllib.parse import urljoin

from django.conf import settings
from django.utils.dateformat import format as format_date
from mtp_common import nomis
from mtp_common.auth.api_client import get_api_session_with_session
from mtp_common.spooling import spoolable
from mtp_common.tasks import send_email
from mtp_common.utils import format_currency
import requests
from requests.exceptions import HTTPError, RequestException

logger = logging.getLogger('mtp')

thread_local = local()
thread_local.nomis_session = requests.Session()


@spoolable(body_params=('user', 'user_session', 'selected_credit_ids', 'credits',))
def credit_selected_credits_to_nomis(*, user, user_session, selected_credit_ids, credits):
    credited = 0
    for credit_id in selected_credit_ids:
        if credit_id in credits:
            credit_individual_credit_to_nomis(user, user_session, credit_id, credits[credit_id])
            credited += 1
        else:
            logger.warning('Credit %(credit_id)s is no longer available', {'credit_id': credit_id})
    logger.info('Credited %(count)d credits', {'count': credited})

    if settings.PRISONER_CAPPING_ENABLED:
        prisoner_locations = set(
            (credit['prison'], credit['prisoner_number'])
            for credit in credits.values()
        )
        for prison, prisoner_number in prisoner_locations:
            check_balance_is_below_cap(prison, prisoner_number)


@spoolable()
def credit_individual_credit_to_nomis(user, user_session, credit_id, credit):
    api_session = get_api_session_with_session(user, user_session)
    if not hasattr(thread_local, 'nomis_session'):
        thread_local.nomis_session = requests.Session()

    nomis_response = None
    try:
        nomis_response = nomis.create_transaction(
            prison_id=credit['prison'],
            prisoner_number=credit['prisoner_number'],
            amount=credit['amount'],
            record_id=str(credit_id),
            description='Sent by {sender}'.format(sender=credit['sender_name']),
            transaction_type='MTDS',
            retries=1,
            session=thread_local.nomis_session
        )
    except HTTPError as e:
        if e.response.status_code == 409:
            logger.warning('Credit %(credit_id)s was already present in NOMIS', {'credit_id': credit_id})
        elif e.response.status_code >= 500:
            logger.error('Credit %(credit_id)s could not credited as NOMIS is unavailable', {'credit_id': credit_id})
            return
        else:
            logger.warning('Credit %(credit_id)s cannot be automatically credited to NOMIS', {'credit_id': credit_id})
            api_session.post(
                'credits/actions/setmanual/',
                json={'credit_ids': [int(credit_id)]}
            )
            return
    except RequestException:
        logger.exception('Credit %(credit_id)s could not credited as NOMIS is unavailable', {'credit_id': credit_id})
        return

    credit_update = {'id': credit_id, 'credited': True}
    if nomis_response and 'id' in nomis_response:
        credit_update['nomis_transaction_id'] = nomis_response['id']
    api_session.post('credits/actions/credit/', json=[credit_update])

    if credit.get('sender_email'):
        ref_number = credit.get('short_payment_ref') or ''
        prisoner_name = credit.get('intended_recipient') or ''
        send_email(
            template_name='cashbook-credited-confirmation',
            to=credit['sender_email'],
            personalisation={
                'amount': format_currency(credit['amount']),
                'has_ref_number': 'yes' if ref_number else 'no',
                'ref_number': ref_number,
                'received_at': format_date(credit['received_at'], 'd/m/Y'),
                'has_prisoner_name': 'yes' if prisoner_name else 'no',
                'prisoner_name': prisoner_name,
                'help_url': urljoin(settings.SEND_MONEY_URL, '/help/'),
                'site_url': settings.START_PAGE_URL,
            },
            reference=f'credited-{credit_id}',
            staff_email=False,
        )


NOMIS_ACCOUNTS = {'cash', 'spends', 'savings'}


@spoolable()
def check_balance_is_below_cap(prison, prisoner_number):
    # NB: balances are not known in private estate currently, but cashbook is not used in there
    try:
        nomis_account_balances = nomis.get_account_balances(prison, prisoner_number)
        assert set(nomis_account_balances.keys()) == NOMIS_ACCOUNTS, 'response keys differ from expected'
        assert all(
            isinstance(nomis_account_balances[account], int) and nomis_account_balances[account] >= 0
            for account in NOMIS_ACCOUNTS
        ), 'not all response values are natural ints'
    except AssertionError as e:
        logger.exception(
            'NOMIS balances for %(prisoner_number)s is malformed',
            {'prisoner_number': prisoner_number, 'exception': e}
        )
    except requests.RequestException:
        logger.exception(
            'Cannot lookup NOMIS balances for %(prisoner_number)s',
            {'prisoner_number': prisoner_number}
        )
    else:
        prisoner_account_balance = sum(nomis_account_balances[account] for account in NOMIS_ACCOUNTS)
        if prisoner_account_balance > settings.PRISONER_CAPPING_THRESHOLD_IN_POUNDS * 100:
            logger.error(
                'NOMIS account balance for %(prisoner_number)s exceeds cap',
                {'prisoner_number': prisoner_number}
            )
