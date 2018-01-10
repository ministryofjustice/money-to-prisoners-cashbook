from mtp_common import nomis
import requests
from requests.exceptions import RequestException


def get_disbursement_viability(request, disbursement):
    viability = {}
    nomis_session = requests.Session()
    try:
        accounts = nomis.get_account_balances(
            disbursement['prison'],
            disbursement['prisoner_number'],
            session=nomis_session
        )

        viability['insufficient_funds'] = (
            disbursement['amount'] > accounts['cash']
        )
    except RequestException:
        pass

    try:
        location = nomis.get_location(disbursement['prisoner_number'])

        viability['prisoner_moved'] = (
            disbursement['prison'] != location['nomis_id']
        )
    except RequestException:
        pass

    viability['self_own'] = (
        disbursement['log_set'][0]['user']['username'] == request.user.username
    )
    viability['editable'] = disbursement['resolution'] == 'pending'
    viability['confirmable'] = disbursement['resolution'] in ('pending', 'preconfirmed')

    viability['viable'] = not (
        viability.get('insufficient_funds', False) or
        viability.get('prisoner_moved', False) or
        viability['self_own']
    ) and viability['confirmable']

    return viability
