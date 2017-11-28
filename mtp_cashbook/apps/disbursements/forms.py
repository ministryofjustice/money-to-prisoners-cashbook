import logging
from math import floor
from decimal import Decimal
from urllib.parse import quote_plus

from django import forms
from extended_choices import Choices
from django.utils.encoding import force_text
from django.utils.translation import gettext_lazy as _
from mtp_common import nomis
from mtp_common.auth.api_client import get_api_session
from mtp_common.auth.exceptions import HttpNotFoundError, Forbidden
from requests.exceptions import RequestException

logger = logging.getLogger('mtp')

SENDING_METHOD = Choices(
    ('BANK_TRANSFER', 'bank_transfer', _('Bank transfer')),
    ('CHEQUE', 'cheque', _('Cheque')),
)


class DisbursementForm(forms.Form):
    @classmethod
    def unserialise_from_session(cls, request, previous_form_data):
        session = request.session

        def get_value(f):
            value = session[f]
            if hasattr(cls, 'unserialise_%s' % f) and value is not None:
                value = getattr(cls, 'unserialise_%s' % f)(value)
            return value

        try:
            data = {
                field: get_value(field)
                for field in cls.base_fields
            }
        except KeyError:
            data = None
        return cls(request=request, data=data, previous_form_data=previous_form_data)

    @classmethod
    def delete_from_session(cls, request):
        for field in cls.base_fields:
            request.session.pop(field, None)

    def __init__(self, request=None, previous_form_data={}, **kwargs):
        super().__init__(**kwargs)
        self.request = request
        self.previous_form_data = previous_form_data

    def serialise_to_session(self):
        cls = self.__class__
        session = self.request.session
        for field in cls.base_fields:
            value = self.cleaned_data[field]
            if hasattr(cls, 'serialise_%s' % field):
                value = getattr(cls, 'serialise_%s' % field)(value)
            session[field] = value


class PrisonerForm(DisbursementForm):
    prisoner_number = forms.CharField(
        label='Prisoner number',
        help_text='For example, A1234BC',
        max_length=7,
    )
    error_messages = {
        'connection': _('This service is currently unavailable'),
        'not_found': _('No prisoner matches the details you’ve supplied'),
        'wrong_prison': _('This prisoner does not appear to be in a prison that you manage'),
    }

    @classmethod
    def delete_from_session(cls, request):
        super().delete_from_session(request)
        request.session.pop('prisoner_name', None)
        request.session.pop('prisoner_dob', None)
        request.session.pop('prison', None)

    def clean_prisoner_number(self):
        prisoner_number = self.cleaned_data.get('prisoner_number')
        if prisoner_number:
            prisoner_number = prisoner_number.upper()
            session = get_api_session(self.request)
            try:
                prisoner = session.get(
                    '/prisoner_locations/{prisoner_number}/'.format(
                        prisoner_number=quote_plus(prisoner_number)
                    )
                ).json()

                self.cleaned_data['prisoner_name'] = prisoner['prisoner_name']
                self.cleaned_data['prisoner_dob'] = prisoner['prisoner_dob']
                self.cleaned_data['prison'] = prisoner['prison']
            except HttpNotFoundError:
                raise forms.ValidationError(
                    self.error_messages['not_found'], code='not_found')
            except Forbidden:
                raise forms.ValidationError(
                    self.error_messages['wrong_prison'], code='wrong_prison')
            except (RequestException, ValueError):
                logger.exception('Could not look up prisoner location')
                raise forms.ValidationError(
                    self.error_messages['connection'], code='connection')
        return prisoner_number


def serialise_amount(amount):
    return '{0:.2f}'.format(amount/100)


def unserialise_amount(amount_text):
    amount_text = force_text(amount_text)
    return Decimal(amount_text)


class AmountForm(DisbursementForm):
    amount = forms.DecimalField(
        label='Amount to send',
        help_text='For example, 10.00',
        min_value=Decimal('0.01'),
        decimal_places=2,
    )
    serialise_amount = serialise_amount
    unserialise_amount = unserialise_amount
    error_messages = {
        'invalid': _('Enter amount as a number'),
        'min_value': _('Amount should be 1p or more'),
        'exceeds_funds': _(
            'There is not enough money in the prisoner’s private account. '
            'Use NOMIS to move money from other accounts into the private '
            'account, then click ’Update balances’'),
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from .views import PrisonerView
        try:
            balances = nomis.get_account_balances(
                self.previous_form_data[PrisonerView.url_name]['prison'],
                self.previous_form_data[PrisonerView.url_name]['prisoner_number']
            )
            self.spends_balance = balances['spends']
            self.private_balance = balances['cash']
            self.savings_balance = balances['savings']
            self.balance_available = True
        except RequestException:
            self.balance_available = False

    def clean_amount(self):
        amount = floor(Decimal(self.cleaned_data['amount'])*100)
        if self.balance_available:
            if amount > self.private_balance:
                raise forms.ValidationError(
                    self.error_messages['exceeds_funds'], code='exceeds_funds')
        return amount


class SendingMethodForm(DisbursementForm):
    sending_method = forms.ChoiceField(
        label='Sending method',
        initial=SENDING_METHOD.BANK_TRANSFER,
        choices=SENDING_METHOD,
        widget=forms.RadioSelect(),
        help_text={
            SENDING_METHOD.BANK_TRANSFER: _(
                'The money will credited directly to the recipient’s bank account.'
            ),
            SENDING_METHOD.CHEQUE: _(
                'The cheque will be issued by SSCL and sent by post to the recipient. '
                'The prisoner doesn’t need to pay for postage.'
            )
        }
    )


class RecipientContactForm(DisbursementForm):
    recipient_name = forms.CharField(label='Their name')
    address_line1 = forms.CharField(label='Their address')
    address_line2 = forms.CharField(required=False)
    city = forms.CharField(required=False)
    postcode = forms.CharField(label='Their postcode')
    email = forms.EmailField(label='Their email address (if provided)', required=False)


class RecipientBankAccountForm(DisbursementForm):
    account_number = forms.CharField(
        label='Bank account number',
        help_text='For example, 09098765'
    )
    sort_code = forms.CharField(
        label='Sort code',
        help_text='For example, 02-02-80'
    )
