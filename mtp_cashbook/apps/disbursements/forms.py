from decimal import Decimal

from django import forms
from django.utils.encoding import force_text


class DisbursementForm(forms.Form):
    @classmethod
    def unserialise_from_session(cls, request):
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
        return cls(request=request, data=data)

    def __init__(self, request=None, **kwargs):
        super().__init__(**kwargs)
        self.request = request

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

    def clean_prisoner_number(self):
        prisoner_number = self.cleaned_data['prisoner_number']
        if prisoner_number == 'A1001AE':
            raise forms.ValidationError('A1001AE Gilly Hall has moved or been released')
        return prisoner_number


def serialise_amount(amount):
    return '{0:.2f}'.format(amount)


def unserialise_amount(amount_text):
    amount_text = force_text(amount_text)
    return Decimal(amount_text)


class AmountForm(DisbursementForm):
    amount = forms.DecimalField(
        label='Amount to send',
        help_text='For example, 10.00',
        min_value=Decimal('0.01'),
        decimal_places=2,
        error_messages={
            'invalid': 'Enter as a number',
            'min_value': 'Amount should be 1p or more',
        }
    )
    serialise_amount = serialise_amount
    unserialise_amount = unserialise_amount

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount >= 30:
            raise forms.ValidationError(
                'A1409AE James Halls has insufficient funds in their spends account'
            )
        return amount


class RecipientContactForm(DisbursementForm):
    recipient_name = forms.CharField(label='Name')
    address_line1 = forms.CharField(label='Address')
    address_line2 = forms.CharField(required=False)
    city = forms.CharField(required=False)
    postcode = forms.CharField(label='Postcode')
    email = forms.CharField(label='Email (if provided)', required=False)


class RecipientBankAccountForm(DisbursementForm):
    account_number = forms.CharField(
        label='Bank account number',
        help_text='For example, 09098765'
    )
    sort_code = forms.CharField(
        label='Sort code',
        help_text='For example, 02-02-80'
    )


class FilterProcessedDisbursementsListForm(forms.Form):
    start = forms.DateField(label='From',
                            help_text='eg 1/6/2017',
                            required=False)
    end = forms.DateField(label='To',
                          help_text='eg 5/6/2017',
                          required=False)


class FilterAllDisbursementsForm(forms.Form):
    start = forms.DateField(label='From date',
                            help_text='eg 1/6/2017',
                            required=False)
    end = forms.DateField(label='To date',
                          help_text='eg 5/6/2017',
                          required=False)
    search = forms.CharField(label='Keywords',
                             help_text='Search all by eg NOMIS ID',
                             required=False)
