from django.urls import reverse
from mtp_common.auth.models import MojUser

from .utils import check_pre_approval_required


def footer_feedback_context(request):
    view_name = request.resolver_match.url_name if request.resolver_match else None
    views_needing_feedback = {'new-credits', 'processed-credits-list', 'processed-credits-detail', 'all-credits'}
    if isinstance(request.user, MojUser) and view_name in views_needing_feedback:
        return {'footer_feedback_context': {
            'submit_url': reverse('submit_footer_feedback'),
        }}
    return {}


def pre_approval_required(request):
    return {'pre_approval_required': check_pre_approval_required(request)}
