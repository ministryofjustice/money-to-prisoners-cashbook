from django.conf import settings
from django.utils.translation import gettext
from mtp_common.context_processors import govuk_localisation as inherited_localisation


def govuk_localisation(request):
    data = inherited_localisation(request)
    data.update(
        homepage_url=data['home_url'],
        logo_link_title=gettext('Go to the homepage'),
        global_header_text=gettext('Manage prisoners’ money'),
    )
    return data


def cashbook_settings(_):
    return {
        'noms_ops_url': settings.NOMS_OPS_URL,
    }
