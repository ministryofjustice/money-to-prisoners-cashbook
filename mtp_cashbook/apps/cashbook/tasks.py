import logging

from django.conf import settings
from django.utils.translation import gettext as _
from mtp_common.auth.api_client import get_connection_with_session
from mtp_common import nomis
from mtp_common.spooling import spoolable
from mtp_common.tasks import send_email
from requests.exceptions import HTTPError

logger = logging.getLogger('mtp')


@spoolable()
def credit_selected_credits_to_nomis(user, session, selected_credit_ids, credits):
    for credit_id in selected_credit_ids:
        if credit_id in credits:
            credit_individual_credit_to_nomis(user, session, credit_id, credits[credit_id])
        else:
            logger.warn('Credit %s is no longer available' % credit_id)


@spoolable()
def credit_individual_credit_to_nomis(user, session, credit_id, credit):
    client = get_connection_with_session(user, session)
    try:
        nomis.credit_prisoner(
            credit['prison'],
            credit['prisoner_number'],
            credit['amount'],
            str(credit_id),
            'Sent by {sender}'.format(sender=credit['sender_name']),
            retries=1
        )
    except HTTPError as e:
        if e.response.status_code == 409:
            logger.warn('Credit %s was already present in NOMIS' % credit_id)
        elif e.response.status_code >= 500:
            logger.error('Credit %s could not credited as NOMIS is unavailable' % credit_id)
            return
        else:
            logger.error('Credit %s cannot be automatically credited to NOMIS' % credit_id)
            client.credits.actions.setmanual.post({
                'credit_ids': [int(credit_id)]
            })
            return

    client.credits.actions.credit.post({
        'credit_ids': [int(credit_id)]
    })
    if credit.get('sender_email'):
        send_email(
            credit['sender_email'], 'cashbook/email/credited-confirmation.txt',
            _('Send money to a prisoner: the prisoner’s account has been credited'),
            context={
                'amount': credit['amount'],
                'ref_number': credit.get('short_ref_number'),
                'received_at': credit['received_at'],
                'prisoner_name': credit['prisoner_name'],
                'help_url': settings.CITIZEN_HELP_PAGE_URL,
                'feedback_url': settings.CITIZEN_CONTACT_PAGE_URL,
                'site_url': settings.START_PAGE_URL,
            },
            html_template='cashbook/email/credited-confirmation.html'
        )
