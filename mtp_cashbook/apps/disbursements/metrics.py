from django.apps import apps
from prometheus_client import Counter

entered_counter = Counter('mtp_cashbook_entered', 'Disbursements entered')
confirmed_counter = Counter('mtp_cashbook_confirmed', 'Disbursements confirmed')
rejected_counter = Counter('mtp_cashbook_rejected', 'Disbursements rejected')

app = apps.get_app_config('metrics')
app.register_collector(entered_counter)
app.register_collector(confirmed_counter)
app.register_collector(rejected_counter)
