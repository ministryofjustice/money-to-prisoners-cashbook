from django.conf import settings
from django.urls import reverse
from mtp_common.context_processors import govuk_localisation as inherited_localisation


def govuk_localisation(request):
    data = inherited_localisation(request)
    data['home_url'] = reverse('home')
    return data


def cashbook_settings(_):
    return {
        'noms_ops_url': settings.NOMS_OPS_URL,
    }
