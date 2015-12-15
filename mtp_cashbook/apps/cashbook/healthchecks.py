from django.conf import settings

from moj_utils.healthchecks import UrlHealthcheck, registry

registry.register_healthcheck(UrlHealthcheck(
    name='api',
    url='%s/healthcheck.json' % settings.API_URL,
    value_at_json_path=(True, '*.status'),
))
