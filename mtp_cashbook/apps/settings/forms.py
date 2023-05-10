from django import forms
from django.utils.translation import gettext_lazy as _


class ChangeCreditNoticeEmailsForm(forms.Form):
    email = forms.EmailField(label=_('New email address'), required=True)
