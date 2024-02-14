from django.conf import settings


def cashbook_settings(_):
    return {
        'noms_ops_url': settings.NOMS_OPS_URL,
        'CASHBOOK_FOOTER_FEEDBACK_LINK': settings.CASHBOOK_FOOTER_FEEDBACK_LINK,
        'DISBURSEMENTS_FOOTER_FEEDBACK_LINK': settings.DISBURSEMENTS_FOOTER_FEEDBACK_LINK,
        'DPS': settings.DPS,
    }
