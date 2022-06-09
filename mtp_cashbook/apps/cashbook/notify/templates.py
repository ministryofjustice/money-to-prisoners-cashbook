import textwrap

from mtp_common.notify.templates import NotifyTemplateRegistry


class CashbookNotifyTemplates(NotifyTemplateRegistry):
    """
    Templates that mtp-cashbook expects to exist in GOV.UK Notify
    """
    templates = {
        'cashbook-credited-confirmation': {
            'subject': 'Send money to someone in prison: the prisoner’s account has been credited',
            'body': textwrap.dedent("""
                Dear sender,

                The payment you made has now been credited to the prisoner’s account.
                ((has_ref_number??Confirmation number: ))((ref_number))
                ((has_prisoner_name??Payment to: ))((prisoner_name))
                Amount paid: ((amount))
                Date payment made: ((received_at))

                Thank you for using this service.

                Help with problems using this service: ((help_url))
                Back to the service: ((site_url))
            """).strip(),
            'personalisation': [
                'has_ref_number', 'ref_number',
                'has_prisoner_name', 'prisoner_name',
                'amount', 'received_at',
                'help_url', 'site_url',
            ],
        },
    }
