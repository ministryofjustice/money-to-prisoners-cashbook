import logging
from threading import local
from urllib.parse import urljoin

from django.conf import settings
from django.utils.translation import gettext as _
from mtp_common.auth.api_client import get_api_session_with_session
from mtp_common import nomis
from mtp_common.spooling import spoolable
from mtp_common.tasks import send_email
import requests
from requests.exceptions import HTTPError, RequestException

from cashbook import metrics

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
            logger.warning('Credit %s is no longer available' % credit_id)
    metrics.credited_summary.observe(credited)


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
            logger.warning('Credit %s was already present in NOMIS' % credit_id)
        elif e.response.status_code >= 500:
            logger.error('Credit %s could not credited as NOMIS is unavailable' % credit_id)
            return
        else:
            logger.warning('Credit %s cannot be automatically credited to NOMIS' % credit_id)
            api_session.post(
                'credits/actions/setmanual/',
                json={'credit_ids': [int(credit_id)]}
            )
            return
    except RequestException:
        logger.exception('Credit %s could not credited as NOMIS is unavailable' % credit_id)
        return

    credit_update = {'id': credit_id, 'credited': True}
    if nomis_response and 'id' in nomis_response:
        credit_update['nomis_transaction_id'] = nomis_response['id']
    api_session.post('credits/actions/credit/', json=[credit_update])

    if credit.get('sender_email'):
        send_email(
            credit['sender_email'], 'cashbook/email/credited-confirmation.txt',
            _('Send money to someone in prison: the prisoner’s account has been credited'),
            context={
                'amount': credit['amount'],
                'ref_number': credit.get('short_ref_number'),
                'received_at': credit['received_at'],
                'prisoner_name': credit.get('intended_recipient'),
                'help_url': urljoin(settings.SEND_MONEY_URL, '/help/'),
                'feedback_url': urljoin(settings.SEND_MONEY_URL, '/contact-us/'),
                'site_url': settings.START_PAGE_URL,
            },
            html_template='cashbook/email/credited-confirmation.html',
            anymail_tags=['credited'],
        )
