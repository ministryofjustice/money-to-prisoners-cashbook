from django.urls import reverse
from mtp_common.auth.models import MojUser

from .utils import nomis_integration_available


def nomis_integration(request):
    return {'nomis_integration_available': nomis_integration_available(request)}


def footer_feedback_context(request):
    view_name = request.resolver_match.url_name if request.resolver_match else None
    if isinstance(request.user, MojUser) and view_name in ('new-credits', 'all-credits'):
        return {'footer_feedback_context': {
            'submit_url': reverse('submit_footer_feedback'),
        }}
    return {}
