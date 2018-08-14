from mtp_common.user_admin.views import SignUpView, AcceptRequestView

from mtp_auth.forms import CashbookSignUpForm


class CashbookSignUpView(SignUpView):
    form_class = CashbookSignUpForm

    def get_context_data(self, **kwargs):
        kwargs['breadcrumbs_back'] = '/'
        return super().get_context_data(**kwargs)


class CashbookAcceptRequestView(AcceptRequestView):
    def get_context_data(self, **kwargs):
        kwargs['account_request_prisons'] = ', '.join(
            prison['name']
            for prison in self.request.user.user_data.get('prisons')
        )
        return super().get_context_data(**kwargs)
