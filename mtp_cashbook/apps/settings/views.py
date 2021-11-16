from mtp_common.auth.api_client import get_api_session
from mtp_common.views import SettingsView


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
