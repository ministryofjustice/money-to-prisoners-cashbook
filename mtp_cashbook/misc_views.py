from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import View, TemplateView
from mtp_common.auth import api_client


class BaseView(View):
    """
    Base class for all cashbook and disbursement views:
    - forces login
    """

    @method_decorator(login_required)
    def dispatch(self, request, **kwargs):
        return super().dispatch(request, **kwargs)


class LandingView(BaseView, TemplateView):
    template_name = 'landing.html'

    def get_context_data(self, **kwargs):
        if self.request.user.has_perm('auth.change_user'):
            response = api_client.get_api_session(self.request).get('requests/', params={'page_size': 1})
            kwargs['user_request_count'] = response.json().get('count')
        return super().get_context_data(
            start_page_url=settings.START_PAGE_URL,
            **kwargs
        )
