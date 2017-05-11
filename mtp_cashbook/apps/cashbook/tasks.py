import logging
from smtplib import SMTPException

from django.conf import settings
from django.utils.translation import gettext as _
from django_mailgun import MailgunAPIError
from mtp_common.auth.api_client import get_connection_with_session
from mtp_common.email import send_email
from mtp_common import nomis
from requests.exceptions import HTTPError, RequestException

logger = logging.getLogger('mtp')


def send_credit_confirmation_email(email, prisoner_name, amount, ref_number, received_at):
    if email:
        try:
            send_email(
                email, 'cashbook/email/credited-confirmation.txt',
                _('Send money to a prisoner: the prisoner’s account has been credited'),
                context={
                    'amount': amount,
                    'ref_number': ref_number,
                    'received_at': received_at,
                    'prisoner_name': prisoner_name,
                    'help_url': settings.CITIZEN_HELP_PAGE_URL,
                    'feedback_url': settings.CITIZEN_CONTACT_PAGE_URL,
                    'site_url': settings.START_PAGE_URL,
                },
                html_template='cashbook/email/credited-confirmation.html'
            )
        except (MailgunAPIError, RequestException, SMTPException):
            logger.exception('Could not send credit credited notification')


def credit_selected_credits_to_nomis(user, session, selected_credit_ids, credits):
    for credit_id in selected_credit_ids:
        if credit_id in credits:
            schedule_credit_individual_credit_to_nomis(user, session, credit_id, credits[credit_id])
        else:
            logger.warn('Credit %s is no longer available' % credit_id)


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
    schedule_credit_confirmation_email(
        credit.get('sender_email'), credit['prisoner_name'],
        credit['amount'], credit.get('short_ref_number'),
        credit['received_at']
    )


try:
    import uwsgi  # noqa
    from mtp_common.uwsgidecorators import spool

    @spool(pass_arguments=True)
    def schedule_credit_confirmation_email(email, prisoner_name, amount, ref_number, received_at):
        if email:
            send_credit_confirmation_email(email, prisoner_name, amount, ref_number, received_at)

    @spool(pass_arguments=True)
    def schedule_credit_selected_credits_to_nomis(user, session, selected_credits, credit_choices):
        credit_selected_credits_to_nomis(user, session, selected_credits, credit_choices)

    @spool(pass_arguments=True)
    def schedule_credit_individual_credit_to_nomis(user, session, credit_id, credit):
        credit_individual_credit_to_nomis(user, session, credit_id, credit)

except ImportError as e:
    schedule_credit_confirmation_email = send_credit_confirmation_email
    schedule_credit_selected_credits_to_nomis = credit_selected_credits_to_nomis
    schedule_credit_individual_credit_to_nomis = credit_individual_credit_to_nomis
