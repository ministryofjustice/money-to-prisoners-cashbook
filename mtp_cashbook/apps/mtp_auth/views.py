from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import FormView
from mtp_common.user_admin.views import SignUpView, AcceptRequestView, ensure_compatible_admin

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


@method_decorator(login_required, name='dispatch')
@method_decorator(ensure_compatible_admin, name='dispatch')
class MovePrisonView(FormView):
    template_name = 'mtp_auth/move-prison.html'
    form_class = CashbookSignUpForm
    success_url = reverse_lazy(settings.LOGIN_REDIRECT_URL)
    success_template_name = 'mtp_common/user_admin/sign-up-success.html'

    def get_initial(self):
        initial = super().get_initial()
        initial.update(
            first_name=self.request.user.user_data['first_name'],
            last_name=self.request.user.user_data['last_name'],
            email=self.request.user.email,
            username=self.request.user.username,
        )
        return initial

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs['request'] = self.request
        return form_kwargs

    def get_context_data(self, **kwargs):
        kwargs['breadcrumbs_back'] = self.success_url
        context_data = super().get_context_data(**kwargs)
        form = context_data['form']
        context_data['hidden_fields'] = [
            form[field]
            for field in ('first_name', 'last_name', 'email', 'username', 'role')
        ]
        return context_data

    def form_valid(self, form):
        return self.response_class(
            request=self.request,
            template=[self.success_template_name],
            context=self.get_context_data(),
            using=self.template_engine,
        )
