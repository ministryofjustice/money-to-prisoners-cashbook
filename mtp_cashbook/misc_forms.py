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
