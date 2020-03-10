from django.conf import settings
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

    change_logs = sorted(
        filter(lambda l: l['action'] in ('created', 'edited'), disbursement['log_set']),
        key=lambda l: l['created']
    )
    viability['self_own'] = (
        change_logs and change_logs[-1]['user']['username'] == request.user.username
    )
    viability['editable'] = disbursement['resolution'] == 'pending'
    viability['confirmable'] = disbursement['resolution'] in ('pending', 'preconfirmed')

    viability['viable'] = not (
        viability.get('insufficient_funds', False) or
        viability.get('prisoner_moved', False) or
        viability['self_own']
    ) and viability['confirmable']

    return viability


def find_addresses(postcode):
    try:
        results = requests.get(
            settings.POSTCODE_LOOKUP_ENDPOINT,
            params={'postcode': postcode, 'key': settings.POSTCODE_LOOKUP_AUTH_TOKEN},
            timeout=5
        )
    except RequestException:
        return []

    addresses = []
    if results.status_code == 200:
        address_results = results.json().get('results', [])
        for result in address_results:
            address_data = result['DPA']

            address = {
                'address': address_data['ADDRESS'],
                'city': address_data['POST_TOWN'],
                'postcode': address_data['POSTCODE'],
            }

            business = build_address_line(
                address_data, 'DEPARTMENT_NAME', 'ORGANISATION_NAME'
            )

            po_box = address_data.get('PO_BOX_NUMBER')

            building = build_address_line(
                address_data, 'SUB_BUILDING_NAME', 'BUILDING_NAME'
            )

            building_number = address_data.get('BUILDING_NUMBER')
            street = build_address_line(
                address_data, 'DEPENDENT_THOROUGHFARE_NAME', 'THOROUGHFARE_NAME'
            )
            if building_number and street:
                street_number = ' '.join([building_number, street])
            else:
                street_number = building_number or street

            locality = build_address_line(
                address_data, 'DOUBLE_DEPENDENT_LOCALITY', 'DEPENDENT_LOCALITY'
            )

            address['address_line1'] = ''
            address['address_line2'] = ''

            items = [
                item for item in
                [business, po_box, building, street_number, locality]
                if item
            ]
            if items:
                address['address_line1'] = items[0]
                address['address_line2'] = ', '.join(items[1:])

            addresses.append(address)

    return addresses


def build_address_line(address_data, *keys):
    items = []
    for key in keys:
        if key in address_data:
            items.append(address_data[key])
    return ', '.join(items) if items else None
