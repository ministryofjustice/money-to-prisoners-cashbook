from django.conf import settings


def cashbook_settings(_):
    return {
        'noms_ops_url': settings.NOMS_OPS_URL,
    }
