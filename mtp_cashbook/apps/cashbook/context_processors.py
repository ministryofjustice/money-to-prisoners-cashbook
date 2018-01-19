from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.translation import gettext
from mtp_common.context_processors import govuk_localisation as inherited_localisation


def govuk_localisation(request):
    global_header_text = gettext('Manage prisoner money')
    if request.disbursements_available and hasattr(request, 'proposition_app'):
        # NB: ensure proposition_app variables are html-safe
        global_header_text += '</a> ' \
                              '<a class="mtp-header-app" href="%(url)s">' \
                              '%(name)s' % request.proposition_app
        global_header_text = mark_safe(global_header_text)
    data = inherited_localisation(request)
    data.update(
        homepage_url=data['home_url'],
        logo_link_title=gettext('Go to the homepage'),
        global_header_text=global_header_text,
    )
    return data


def cashbook_settings(_):
    return {
        'noms_ops_url': settings.NOMS_OPS_URL,
    }
