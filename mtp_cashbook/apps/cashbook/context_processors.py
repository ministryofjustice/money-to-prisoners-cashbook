from django.utils.translation import gettext
from mtp_common.context_processors import govuk_localisation as inherited_localisation

from .utils import check_pre_approval_required


def govuk_localisation(request):
    data = inherited_localisation(request)
    data.update(
        homepage_url=data['home_url'],
        logo_link_title=gettext('Go to the homepage'),
        global_header_text=gettext('Digital cashbook'),
    )
    return data


def pre_approval_required(request):
    return {'pre_approval_required': check_pre_approval_required(request)}
