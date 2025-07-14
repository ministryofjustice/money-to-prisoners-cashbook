from django.conf import settings
from django.utils.translation import gettext


def cashbook_settings(request):
    proposition_title = getattr(request, 'proposition_app', {}).get('name') or gettext('Manage prisoner money')
    return {
        'proposition_title': proposition_title,
        'noms_ops_url': settings.NOMS_OPS_URL,
        'CASHBOOK_FOOTER_FEEDBACK_LINK': settings.CASHBOOK_FOOTER_FEEDBACK_LINK,
        'DISBURSEMENTS_FOOTER_FEEDBACK_LINK': settings.DISBURSEMENTS_FOOTER_FEEDBACK_LINK,
        'DPS': settings.DPS,
    }
