from mtp_common.user_admin.views import SignUpView

from mtp_auth.forms import CashbookSignUpForm


class CashbookSignUpView(SignUpView):
    form_class = CashbookSignUpForm

    def get_context_data(self, **kwargs):
        kwargs['breadcrumbs_back'] = '/'
        return super().get_context_data(**kwargs)
