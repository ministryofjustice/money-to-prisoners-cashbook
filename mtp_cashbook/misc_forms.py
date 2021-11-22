from django import forms
from django.utils.translation import gettext_lazy as _


class MLBriefingConfirmationForm(forms.Form):
    read_briefing = forms.ChoiceField(
        label=_('Have you read the money laundering briefing?'),
        required=True,
        choices=(
            ('yes', _('Yes')),
            ('no', _('No')),
        ), error_messages={
            'required': _('Please select ‘yes’ or ‘no’'),
        },
    )

    def clean_read_briefing(self):
        read_briefing = self.cleaned_data.get('read_briefing')
        if read_briefing:
            read_briefing = read_briefing == 'yes'
        return read_briefing


class ConfirmCreditNoticeEmailsForm(forms.Form):
    change_email = forms.ChoiceField(
        label=_('Do you want to change the email credits slips are sent to?'),
        required=True,
        choices=(
            ('yes', _('Change email')),
            ('no', _('I’m happy with the current email')),
        ), error_messages={
            'required': _('Please select one of the options'),
        },
    )

    def __init__(self, credit_notice_emails_set=True, **kwargs):
        super().__init__(**kwargs)
        if not credit_notice_emails_set:
            self.fields['change_email'].choices = (
                ('yes', _('Yes, add an email address')),
                ('no', _('No, continue without setup')),
            )

    def clean_change_email(self):
        change_email = self.cleaned_data.get('change_email')
        if change_email:
            change_email = change_email == 'yes'
        return change_email
