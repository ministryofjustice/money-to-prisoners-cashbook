from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import View, TemplateView, FormView
from mtp_common.auth import api_client
from mtp_common.auth.api_client import get_api_session

from mtp_cashbook import READ_ML_BRIEFING_FLAG, CONFIRM_CREDIT_NOTICE_EMAIL_FLAG
from mtp_cashbook.misc_forms import MLBriefingConfirmationForm, ConfirmCreditNoticeEmailsForm
from mtp_cashbook.utils import add_user_flag, delete_user_flag, merge_credit_notice_emails_with_user_prisons


class BaseView(View):
    """
    Base class for all cashbook and disbursement views:
    - forces login
    - ensures "read ML briefing" flag is set or redirects to ML briefing confirmation screen
    - ensures "needs to confirm credit notice emails" flag is not set or redirects to confirmation screen
    """

    @method_decorator(login_required)
    def dispatch(self, request, **kwargs):
        ignore_modal_redirects = getattr(self, 'ignore_modal_redirects', False)
        if not request.read_ml_briefing and not ignore_modal_redirects:
            return redirect('ml-briefing-confirmation')
        if request.confirm_credit_notice_email and not ignore_modal_redirects:
            return redirect('confirm-credit-notice-emails')
        return super().dispatch(request, **kwargs)


class LandingView(BaseView, TemplateView):
    template_name = 'landing.html'

    def get_context_data(self, **kwargs):
        if self.request.user.has_perm('auth.change_user'):
            response = api_client.get_api_session(self.request).get('requests/', params={'page_size': 1})
            kwargs['user_request_count'] = response.json().get('count')

        cards = [
            {
                'heading': _('Digital cashbook'),
                'link': reverse_lazy('new-credits'),
                'description': _('Credit money into a prisoner’s account'),
            },
            {
                'heading': _('Digital disbursements'),
                'link': reverse_lazy('disbursements:start'),
                'description': _('Send money out of a prisoner’s account by bank transfer or cheque'),
            },
        ]

        kwargs.update(
            start_page_url=settings.START_PAGE_URL,
            cards=cards,
        )
        return super().get_context_data(**kwargs)


class MLBriefingConfirmationView(BaseView, FormView):
    title = _('Have you read the money laundering briefing?')
    form_class = MLBriefingConfirmationForm
    template_name = 'ml-briefing-confirmation.html'
    success_url = reverse_lazy('home')

    ignore_modal_redirects = True

    def dispatch(self, request, **kwargs):
        if request.read_ml_briefing:
            return redirect(self.get_success_url())
        return super().dispatch(request, **kwargs)

    def form_valid(self, form):
        read_briefing = form.cleaned_data['read_briefing']
        if read_briefing:
            add_user_flag(self.request, READ_ML_BRIEFING_FLAG)
            messages.success(self.request, _('Thank you, please carry on with your work.'))
            return super().form_valid(form)
        else:
            return redirect('ml-briefing')


class MLBriefingView(BaseView, TemplateView):
    title = _('You need to read the money laundering briefing')
    template_name = 'ml-briefing.html'

    ignore_modal_redirects = True

    def dispatch(self, request, **kwargs):
        if request.read_ml_briefing:
            return redirect(MLBriefingConfirmationView.success_url)
        return super().dispatch(request, **kwargs)


class ConfirmCreditNoticeEmailsView(BaseView, FormView):
    title = _('Email address for credit slips')
    form_class = ConfirmCreditNoticeEmailsForm
    template_name = 'confirm-credit-notice-emails.html'
    success_url = reverse_lazy('home')

    ignore_modal_redirects = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.credit_notice_emails = []

    def dispatch(self, request, **kwargs):
        if not request.confirm_credit_notice_email:
            return redirect(self.get_success_url())

        session = get_api_session(self.request)
        self.credit_notice_emails = session.get('/prisoner_credit_notice_email/').json()

        return super().dispatch(request, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['credit_notice_emails'] = merge_credit_notice_emails_with_user_prisons(
            self.credit_notice_emails, self.request,
        )
        return context

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs['credit_notice_emails_set'] = bool(self.credit_notice_emails)
        return form_kwargs

    def form_valid(self, form):
        delete_user_flag(self.request, CONFIRM_CREDIT_NOTICE_EMAIL_FLAG)
        change_email = form.cleaned_data['change_email']
        if change_email:
            return redirect('credit-notice-emails')
        return super().form_valid(form)


class PolicyChangeInfo(BaseView, TemplateView):
    if settings.BANK_TRANSFERS_ENABLED:
        title = _('How Nov 2nd policy changes will affect you')
    else:
        title = _('Policy changes made on Nov 2nd 2020 that may affect your work')

    def get_template_names(self):
        if settings.BANK_TRANSFERS_ENABLED:
            return ['policy-change-warning.html']
        else:
            return ['policy-change-info.html']


class FAQView(TemplateView):
    title = _('What do you need help with?')
    template_name = 'faq.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['breadcrumbs_back'] = reverse_lazy('home')
        context['reset_password_url'] = reverse_lazy('reset_password')
        context['sign_up_url'] = reverse_lazy('sign-up')

        return context
