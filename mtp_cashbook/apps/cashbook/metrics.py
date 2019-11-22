from django.apps import apps
from prometheus_client import Summary

credited_summary = Summary('mtp_cashbook_credited', 'Credits credited')

app = apps.get_app_config('metrics')
app.register_collector(credited_summary)
