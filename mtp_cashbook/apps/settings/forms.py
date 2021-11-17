from django import forms
from django.utils.translation import gettext_lazy as _
from form_error_reporting import GARequestErrorReportingMixin


class ChangeCreditNoticeEmailsForm(GARequestErrorReportingMixin, forms.Form):
    email = forms.EmailField(label=_('New email address'), required=True)
