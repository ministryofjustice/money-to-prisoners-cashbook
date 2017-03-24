import logging
from smtplib import SMTPException

from django.conf import settings
from django.utils.translation import gettext as _
from django_mailgun import MailgunAPIError
from mtp_common.email import send_email
from requests.exceptions import RequestException

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


try:
    import uwsgi  # noqa
    from mtp_common.uwsgidecorators import spool

    @spool(pass_arguments=True)
    def schedule_credit_confirmation_email(email, prisoner_name, amount, ref_number, received_at):
        if email:
            send_credit_confirmation_email(email, prisoner_name, amount, ref_number, received_at)
except ImportError as e:
    schedule_credit_confirmation_email = send_credit_confirmation_email
