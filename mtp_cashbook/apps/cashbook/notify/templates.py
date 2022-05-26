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

                ---

                Take part in research and receive a £30 gift voucher

                We are carrying out research to understand how we can improve
                prison services. If you have visited a friend or family member
                in prison in the last six months or are planning to do so
                in the next 12 months, we’d like to hear from you.

                Please fill out our quick screener to see if you are eligible for one of our upcoming research studies.
                https://eu.surveymonkey.com/r/7FRLB95
            """).strip(),
            'personalisation': [
                'has_ref_number', 'ref_number',
                'has_prisoner_name', 'prisoner_name',
                'amount', 'received_at',
                'help_url', 'site_url',
            ],
        },
    }
