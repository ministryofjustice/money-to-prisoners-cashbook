from django.conf import settings

from moj_irat.healthchecks import HealthcheckResponse, UrlHealthcheck, registry
from zendesk_tickets.client import zendesk_auth

registry.register_healthcheck(UrlHealthcheck(
    name='api',
    url='%s/healthcheck.json' % settings.API_URL,
    value_at_json_path=(True, '*.status'),
))

if settings.ZENDESK_API_USERNAME and settings.ZENDESK_API_TOKEN and \
        settings.ZENDESK_GROUP_ID:
    registry.register_healthcheck(UrlHealthcheck(
        name='zendesk',
        url='%(base_url)s/api/v2/groups/%(group_id)s.json' % {
            'base_url': settings.ZENDESK_BASE_URL,
            'group_id': settings.ZENDESK_GROUP_ID,
        },
        headers={'Content-Type': 'application/json'},
        auth=zendesk_auth(),
        value_at_json_path=(settings.ZENDESK_GROUP_ID, 'group.id')
    ))
else:
    registry.register_healthcheck(lambda: HealthcheckResponse(
        name='zendesk',
        status=False,
        error='Zendesk API settings not specified',
    ))
