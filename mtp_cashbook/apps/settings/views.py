import logging

from django.contrib import messages
from django.http import Http404
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView
from mtp_common.auth.api_client import get_api_session
from mtp_common.views import SettingsView
from requests.exceptions import HTTPError

from mtp_cashbook.misc_views import BaseView
from settings.forms import ChangeCreditNoticeEmailsForm

logger = logging.getLogger('mtp')


def can_edit_credit_notice_emails(request):
    return bool(request.user.user_data.get('user_admin'))


class CashbookSettingsView(SettingsView):
    template_name = 'settings/settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['can_edit_credit_notice_emails'] = can_edit_credit_notice_emails(self.request)
        if context['can_edit_credit_notice_emails']:
            session = get_api_session(self.request)
            context['credit_notice_emails'] = session.get('/prisoner_credit_notice_email/').json()

        return context


class ChangeCreditNoticeEmailsView(BaseView, FormView):
    title = _('Email address for credit slips')
    form_class = ChangeCreditNoticeEmailsForm
    template_name = 'settings/change-credit-notice-emails.html'
    success_url = reverse_lazy('settings')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.session = None

    def dispatch(self, request, **kwargs):
        if not can_edit_credit_notice_emails(request):
            raise Http404
        self.session = get_api_session(self.request)
        return super().dispatch(request, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = self.success_url
        context['breadcrumbs'] = [
            {'name': _('Home'), 'url': '/'},
            {'name': _('Settings'), 'url': self.success_url},
            {'name': self.title},
        ]
        return context

    def get_initial(self):
        initial = super().get_initial()

        # arbitrarily pick first as initial form value
        credit_notice_emails = self.session.get('/prisoner_credit_notice_email/').json()
        for credit_notice_email in credit_notice_emails:
            initial['email'] = credit_notice_email['email']
            break

        return initial

    def form_valid(self, form):
        patch_data = {'email': form.cleaned_data['email']}

        user_prisons = self.request.user.user_data.get('prisons') or []
        for user_prison in user_prisons:
            prison_id = user_prison['nomis_id']
            try:
                response = self.session.patch(f'/prisoner_credit_notice_email/{prison_id}/', json=patch_data)
                if response.status_code != 200:
                    raise HTTPError(response=response)
            except HTTPError as e:
                logger.error(f'Error patching credit notice email: {e.response.text}')
                form.add_error(None, _('Could not save email for %(name)s') % user_prison)
                return self.form_invalid(form)

        messages.success(self.request, _('Email address for credit slips changed'))
        return super().form_valid(form)
