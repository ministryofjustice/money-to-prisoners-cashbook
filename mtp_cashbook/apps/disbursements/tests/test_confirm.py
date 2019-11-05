from functools import partial
from unittest import mock

from django.urls import reverse
from mtp_common.test_utils import silence_logger
from requests.exceptions import HTTPError
import responses

from cashbook.tests import MTPBaseTestCase, api_url


SAMPLE_DISBURSEMENTS = [
    # last edited by self
    {
        'id': 631,
        'method': 'bank_transfer',
        'amount': 3200,
        'resolution': 'pending',
        'nomis_transaction_id': None,
        'prison': 'BXI',
        'prisoner_name': 'EDWARD WEBBER',
        'prisoner_number': 'A1407AE',
        'recipient_is_company': False,
        'recipient_first_name': 'Geoffrey',
        'recipient_last_name': 'Jennings',
        'address_line1': '632 Shane stravenue',
        'address_line2': '',
        'city': 'Lake Louisville',
        'postcode': 'N2K 9FX',
        'country': 'UK',
        'recipient_email': 'Geoffrey.Jennings@mail.local',
        'remittance_description': 'Payment from EDWARD WEBBER',
        'roll_number': '',
        'sort_code': '11-11-11',
        'account_number': '11111111',
        'created': '2017-12-21T02:53:27.144166Z',
        'modified': '2018-01-11T16:37:45.581101Z',
        'log_set': [
            {
                'user': {
                    'last_name': 'Clerk',
                    'username': 'test-hmp-brixton',
                    'first_name': 'HMP BRIXTON'
                },
                'created': '2017-12-21T02:53:27.144166Z',
                'action': 'created'
            },
            {
                'user': {
                    'last_name': 'Clerk A',
                    'username': 'test-hmp-brixton-a',
                    'first_name': 'HMP BRIXTON'
                },
                'created': '2018-01-11T15:18:09.994500Z',
                'action': 'edited'
            },
        ]
    },
    # prisoner moved
    {
        'id': 646,
        'method': 'bank_transfer',
        'amount': 4000,
        'resolution': 'pending',
        'nomis_transaction_id': None,
        'prison': 'BXI',
        'prisoner_name': 'PRISONER MOVED',
        'prisoner_number': 'A1403AE',
        'recipient_is_company': False,
        'recipient_first_name': 'Angela',
        'recipient_last_name': 'Wood',
        'address_line1': 'Flat 66x',
        'address_line2': 'Nolan grove',
        'city': 'Alexanderbury',
        'postcode': 'N21 7SS',
        'country': 'UK',
        'recipient_email': 'Angela.Wood@mail.local',
        'remittance_description': '',
        'account_number': '89851042',
        'sort_code': '772930',
        'roll_number': None,
        'created': '2017-12-21T00:53:27.150381Z',
        'modified': '2017-12-21T00:53:27.150381Z',
        'log_set': [
            {
                'user': {
                    'last_name': 'Clerk',
                    'username': 'test-hmp-brixton',
                    'first_name': 'HMP BRIXTON'
                },
                'created': '2017-12-21T00:53:27.150381Z',
                'action': 'created'
            }
        ]
    },
    # insufficient funds
    {
        'id': 650,
        'method': 'bank_transfer',
        'amount': 200000,
        'resolution': 'pending',
        'nomis_transaction_id': None,
        'prison': 'BXI',
        'prisoner_name': 'SOID4 CHTEST',
        'prisoner_number': 'A3530AE',
        'recipient_is_company': False,
        'recipient_first_name': 'Jessica',
        'recipient_last_name': 'Hill',
        'address_line1': 'Flat 6',
        'address_line2': 'Carpenter manor',
        'city': 'North Marcusfort',
        'postcode': 'IM0M 2TJ',
        'country': 'UK',
        'recipient_email': None,
        'remittance_description': 'Payment from SOID4 CHTEST',
        'sort_code': '601368',
        'account_number': '19621156',
        'roll_number': None,
        'created': '2017-12-21T09:53:27.151244Z',
        'modified': '2017-12-21T09:53:27.151244Z',
        'log_set': [
            {
                'user': {
                    'last_name': 'Clerk',
                    'username': 'test-hmp-brixton',
                    'first_name': 'HMP BRIXTON'
                },
                'created': '2017-12-21T09:53:27.151244Z',
                'action': 'created'
            }
        ]
    },
    # bank transfer
    {
        'id': 654,
        'method': 'bank_transfer',
        'amount': 3000,
        'resolution': 'pending',
        'nomis_transaction_id': None,
        'prison': 'BXI',
        'prisoner_name': 'TEST ASSESSMENT',
        'prisoner_number': 'A1433AE',
        'recipient_is_company': False,
        'recipient_first_name': 'Ross',
        'recipient_last_name': 'Johnson',
        'address_line1': '460 Johnson springs',
        'address_line2': '',
        'city': 'South Georgia',
        'postcode': 'E09 5SP',
        'country': 'UK',
        'recipient_email': 'Ross.Johnson@mail.local',
        'remittance_description': 'PAYMENT FOR HOUSING',
        'sort_code': '631535',
        'roll_number': None,
        'account_number': '91673671',
        'created': '2017-12-21T05:09:27.152774Z',
        'modified': '2017-12-21T05:09:27.152774Z',
        'log_set': [
            {
                'user': {
                    'last_name': 'Clerk',
                    'username': 'test-hmp-brixton',
                    'first_name': 'HMP BRIXTON'
                },
                'created': '2017-12-21T05:09:27.152774Z',
                'action': 'created'
            }
        ]
    },
    # cheque
    {
        'id': 660,
        'method': 'cheque',
        'amount': 3000,
        'resolution': 'pending',
        'nomis_transaction_id': None,
        'prison': 'BXI',
        'prisoner_name': 'TEST QUASH2',
        'prisoner_number': 'A1448AE',
        'recipient_is_company': False,
        'recipient_first_name': 'Katy',
        'recipient_last_name': 'Hicks',
        'address_line1': '4 Morris spurs',
        'address_line2': '',
        'city': 'Jennaview',
        'postcode': 'L8 0NY',
        'country': 'UK',
        'recipient_email': 'Katy.Hicks@mail.local',
        'remittance_description': 'Payment from TEST QUASH2',
        'sort_code': None,
        'account_number': None,
        'roll_number': None,
        'created': '2017-12-21T04:32:27.154403Z',
        'modified': '2017-12-21T04:32:27.154403Z',
        'log_set': [
            {
                'user': {
                    'last_name': 'Clerk',
                    'username': 'test-hmp-brixton',
                    'first_name': 'HMP BRIXTON'
                },
                'created': '2017-12-21T04:32:27.154403Z',
                'action': 'created'
            }
        ]
    },
    # cheque and company
    {
        'id': 660,
        'method': 'cheque',
        'amount': 3000,
        'resolution': 'pending',
        'nomis_transaction_id': None,
        'prison': 'BXI',
        'prisoner_name': 'TEST QUASH2',
        'prisoner_number': 'A1448AE',
        'recipient_is_company': True,
        'recipient_first_name': '',
        'recipient_last_name': 'Boots',
        'address_line1': '4 Morris spurs',
        'address_line2': '',
        'city': 'Jennaview',
        'postcode': 'L8 0NY',
        'country': 'UK',
        'recipient_email': '',
        'remittance_description': 'Payment from TEST QUASH2',
        'sort_code': None,
        'account_number': None,
        'roll_number': None,
        'created': '2017-12-21T04:32:27.154403Z',
        'modified': '2017-12-21T04:32:27.154403Z',
        'log_set': [
            {
                'user': {
                    'last_name': 'Clerk',
                    'username': 'test-hmp-brixton',
                    'first_name': 'HMP BRIXTON'
                },
                'created': '2017-12-21T04:32:27.154403Z',
                'action': 'created'
            }
        ]
    },
]


class PendingDisbursementTestCase(MTPBaseTestCase):
    def prisoner_location_response(self, disbursement):
        responses.add(
            responses.GET,
            api_url('/prisoner_locations/{prisoner_number}/'.format(
                prisoner_number=disbursement['prisoner_number']
            )),
            json={
                'prisoner_number': disbursement['prisoner_number'],
                'prisoner_dob': '1970-01-01',
                'prisoner_name': 'TEST QUASH2',
                'prison': 'BXI'
            },
            status=200,
        )


def mock_nomis_responses_for_disbursement(mock_nomis_get_account_balances, mock_nomis_get_location, disbursement):
    if disbursement['prisoner_name'] == 'PRISONER MOVED':
        mock_nomis_get_account_balances.side_effect = HTTPError(
            response=mock.Mock(
                status_code=500,
            ),
        )
    else:
        mock_nomis_get_account_balances.return_value = {
            'cash': 10000,
            'spends': 2000,
            'savings': 10000,
        }

    mock_nomis_get_location.return_value = {
        'nomis_id': (
            'LEI'
            if disbursement['prisoner_name'] == 'PRISONER MOVED'
            else disbursement['prison']
        ),
        'name': 'HMP',
    }


def mock_pending_list(func):
    def mocker(mock_nomis_get_account_balances, mock_nomis_get_location, disbursements, preconfirmed=None):
        preconfirmed = preconfirmed or []

        responses.add(
            responses.GET,
            api_url('/disbursements/?resolution=pending&offset=0&limit=100'),
            match_querystring=True,
            json={
                'count': len(disbursements),
                'results': disbursements
            },
            status=200
        )

        responses.add(
            responses.GET,
            api_url('/disbursements/?resolution=preconfirmed&offset=0&limit=100'),
            match_querystring=True,
            json={
                'count': len(preconfirmed),
                'results': preconfirmed
            },
            status=200
        )

        for disbursement in (disbursements + preconfirmed):
            mock_nomis_responses_for_disbursement(
                mock_nomis_get_account_balances,
                mock_nomis_get_location,
                disbursement,
            )

    @responses.activate
    @mock.patch('disbursements.utils.nomis.get_location')
    @mock.patch('disbursements.utils.nomis.get_account_balances')
    def wrapper(self, mock_nomis_get_account_balances, mock_nomis_get_location, *args, **kwargs):
        func(
            self,
            partial(mocker, mock_nomis_get_account_balances, mock_nomis_get_location),
            *args,
            **kwargs,
        )

    return wrapper


def mock_pending_detail(func):
    def mocker(mock_nomis_get_account_balances, mock_nomis_get_location, disbursement):
        responses.add(
            responses.GET,
            api_url('/disbursements/{pk}/'.format(pk=disbursement['id'])),
            json=disbursement,
            status=200
        )
        mock_nomis_responses_for_disbursement(mock_nomis_get_account_balances, mock_nomis_get_location, disbursement)

    @responses.activate
    @mock.patch('disbursements.utils.nomis.get_location')
    @mock.patch('disbursements.utils.nomis.get_account_balances')
    def wrapper(self, mock_nomis_get_account_balances, mock_nomis_get_location, *args, **kwargs):
        func(
            self,
            partial(mocker, mock_nomis_get_account_balances, mock_nomis_get_location),
            *args,
            **kwargs,
        )

    return wrapper


class PendingListDisbursementTestCase(PendingDisbursementTestCase):

    @property
    def url(self):
        return reverse('disbursements:pending_list')

    @mock_pending_list
    def test_display_pending_disbursements(self, calls_mocker):
        self.login(credentials={'username': 'test-hmp-brixton-a', 'password': 'pass'})
        calls_mocker(disbursements=[SAMPLE_DISBURSEMENTS[3], SAMPLE_DISBURSEMENTS[4]])

        response = self.client.get(self.url)
        self.assertOnPage(response, 'disbursements:pending_list')

        self.assertContains(response, 'Confirmation required')

    @mock_pending_list
    def test_pending_list_self_own(self, calls_mocker):
        self.login(credentials={'username': 'test-hmp-brixton-a', 'password': 'pass'})
        calls_mocker(disbursements=[SAMPLE_DISBURSEMENTS[0]])

        response = self.client.get(self.url)
        self.assertOnPage(response, 'disbursements:pending_list')

        self.assertContains(response, 'Another colleague needs to confirm this payment')

    @mock_pending_list
    def test_pending_list_prisoner_moved(self, calls_mocker):
        self.login(credentials={'username': 'test-hmp-brixton-a', 'password': 'pass'})
        calls_mocker(disbursements=[SAMPLE_DISBURSEMENTS[1]])

        response = self.client.get(self.url)
        self.assertOnPage(response, 'disbursements:pending_list')

        self.assertContains(response, 'Prisoner no longer in  this prison')

    @mock_pending_list
    def test_pending_list_with_insufficient_funds(self, calls_mocker):
        self.login(credentials={'username': 'test-hmp-brixton-a', 'password': 'pass'})
        calls_mocker(disbursements=[SAMPLE_DISBURSEMENTS[2]])

        response = self.client.get(self.url)
        self.assertOnPage(response, 'disbursements:pending_list')

        self.assertContains(response, 'Insufficient funds')


class PendingDetailDisbursementTestCase(PendingDisbursementTestCase):

    def url(self, pk):
        return reverse('disbursements:pending_detail', args=[pk])

    @mock_pending_detail
    def test_valid_pending_disbursement(self, calls_mocker):
        self.login(credentials={'username': 'test-hmp-brixton-a', 'password': 'pass'})
        disbursement = SAMPLE_DISBURSEMENTS[3]
        calls_mocker(disbursement)

        response = self.client.get(self.url(disbursement['id']))
        self.assertOnPage(response, 'disbursements:pending_detail')
        self.assertContains(response, 'Confirm payment')
        self.assertContains(response, 'PAYMENT FOR HOUSING')

    @mock_pending_detail
    def test_insufficient_funds_pending_disbursement(self, calls_mocker):
        self.login(credentials={'username': 'test-hmp-brixton-a', 'password': 'pass'})
        disbursement = SAMPLE_DISBURSEMENTS[2]
        calls_mocker(disbursement)

        response = self.client.get(self.url(disbursement['id']))
        self.assertOnPage(response, 'disbursements:pending_detail')
        self.assertContains(
            response, 'There is not enough money in the prisoner’s private account.'
        )
        self.assertNotContains(
            response,
            '<input type="submit" value="Confirm payment" />',
            html=True
        )


class UpdatePendingDisbursementTestCase(PendingDisbursementTestCase):

    @mock_pending_detail
    def test_update_prisoner(self, calls_mocker):
        self.login(credentials={'username': 'test-hmp-brixton-a', 'password': 'pass'})

        # go to update page
        disbursement = SAMPLE_DISBURSEMENTS[3]
        calls_mocker(disbursement)
        responses.add(
            responses.GET,
            api_url('/prisoner_locations/{prisoner_number}/'.format(
                prisoner_number=disbursement['prisoner_number']
            )),
            json={
                'prisoner_number': disbursement['prisoner_number'],
                'prisoner_dob': '1970-01-01',
                'prisoner_name': 'JILLY HALL',
                'prison': 'BXI'
            },
            status=200,
        )

        response = self.client.get(
            reverse('disbursements:update_prisoner', args=[disbursement['id']])
        )
        self.assertContains(response, disbursement['prisoner_number'])

        responses.reset()

        # post update
        new_prisoner_number = 'A1401AE'
        responses.add(
            responses.GET,
            api_url('/prisoner_locations/{prisoner_number}/'.format(
                prisoner_number=new_prisoner_number
            )),
            json={
                'prisoner_number': new_prisoner_number,
                'prisoner_dob': '1970-01-01',
                'prisoner_name': 'JILLY HALL',
                'prison': 'BXI'
            },
            status=200,
        )
        responses.add(
            responses.PATCH,
            api_url('/disbursements/{pk}/'.format(pk=disbursement['id'])),
            status=200
        )

        updated_disbursement = dict(**disbursement)
        updated_disbursement['prisoner_number'] = new_prisoner_number
        updated_disbursement['prisoner_name'] = 'JILLY HALL'
        calls_mocker(updated_disbursement)

        response = self.client.post(
            reverse('disbursements:update_prisoner', args=[updated_disbursement['id']]),
            data={'prisoner_number': new_prisoner_number}, follow=True
        )
        self.assertOnPage(response, 'disbursements:pending_detail')
        self.assertContains(response, new_prisoner_number)

    @mock_pending_detail
    def test_update_person_to_company(self, calls_mocker):
        self.login(credentials={'username': 'test-hmp-brixton-a', 'password': 'pass'})

        # go to update page
        disbursement = SAMPLE_DISBURSEMENTS[3]
        calls_mocker(disbursement)
        responses.add(
            responses.GET,
            api_url('/prisoner_locations/{prisoner_number}/'.format(
                prisoner_number=disbursement['prisoner_number']
            )),
            json={
                'prisoner_number': disbursement['prisoner_number'],
                'prisoner_dob': '1970-01-01',
                'prisoner_name': 'TEST QUASH2',
                'prison': 'BXI'
            },
            status=200,
        )

        response = self.client.get(
            reverse('disbursements:update_recipient_contact', args=[disbursement['id']]),
        )

        self.assertContains(response, disbursement['recipient_first_name'])
        self.assertContains(response, disbursement['recipient_last_name'])
        self.assertOnPage(response, 'disbursements:update_recipient_contact')

        responses.reset()

        # post update
        responses.add(
            responses.GET,
            api_url('/prisoner_locations/{prisoner_number}/'.format(
                prisoner_number=disbursement['prisoner_number']
            )),
            json={
                'prisoner_number': disbursement['prisoner_number'],
                'prisoner_dob': '1970-01-01',
                'prisoner_name': 'TEST QUASH2',
                'prison': 'BXI'
            },
            status=200,
        )
        responses.add(
            responses.PATCH,
            api_url('/disbursements/{pk}/'.format(pk=disbursement['id'])),
            status=200
        )

        new_recipient_type = 'company'
        new_recipient_company_name = 'Boots'
        calls_mocker(disbursement)

        response = self.client.post(
            reverse('disbursements:update_recipient_contact', args=[disbursement['id']]),
            data={
                'recipient_type': new_recipient_type,
                'recipient_company_name': new_recipient_company_name,
                'recipient_first_name': '',
                'recipient_last_name': '',
                'address_line1': '460 Johnson springs',
                'address_line2': '',
                'city': 'South Georgia',
                'postcode': 'E09 5SP',
                'recipient_email': 'Ross.Johnson@mail.local',
            },
            follow=True
        )

        self.assertOnPage(response, 'disbursements:pending_detail')

        patch_requests = [call.request for call in responses.calls if call.request.method == responses.PATCH]
        self.assertEqual(len(patch_requests), 1)
        self.assertJSONEqual(patch_requests[0].body.decode(), {
            'recipient_is_company': True,
            'recipient_first_name': '',
            'recipient_last_name': new_recipient_company_name,
        })

    @mock_pending_detail
    def test_update_company_to_person(self, calls_mocker):
        self.login(credentials={'username': 'test-hmp-brixton-a', 'password': 'pass'})

        # go to update page
        disbursement = SAMPLE_DISBURSEMENTS[5]
        calls_mocker(disbursement)
        responses.add(
            responses.GET,
            api_url('/prisoner_locations/{prisoner_number}/'.format(
                prisoner_number=disbursement['prisoner_number']
            )),
            json={
                'prisoner_number': disbursement['prisoner_number'],
                'prisoner_dob': '1970-01-01',
                'prisoner_name': 'TEST QUASH2',
                'prison': 'BXI'
            },
            status=200,
        )

        response = self.client.get(
            reverse('disbursements:update_recipient_contact', args=[disbursement['id']]),
        )

        self.assertContains(response, disbursement['recipient_last_name'])
        self.assertOnPage(response, 'disbursements:update_recipient_contact')

        responses.reset()

        # post update
        responses.add(
            responses.GET,
            api_url('/prisoner_locations/{prisoner_number}/'.format(
                prisoner_number=disbursement['prisoner_number']
            )),
            json={
                'prisoner_number': disbursement['prisoner_number'],
                'prisoner_dob': '1970-01-01',
                'prisoner_name': 'TEST QUASH2',
                'prison': 'BXI'
            },
            status=200,
        )
        responses.add(
            responses.PATCH,
            api_url('/disbursements/{pk}/'.format(pk=disbursement['id'])),
            status=200
        )

        new_recipient_type = 'person'
        new_recipient_first_name = 'Joe'
        new_recipient_last_name = 'Smith'
        calls_mocker(disbursement)

        response = self.client.post(
            reverse('disbursements:update_recipient_contact', args=[disbursement['id']]),
            data={
                'recipient_type': new_recipient_type,
                'recipient_first_name': new_recipient_first_name,
                'recipient_last_name': new_recipient_last_name,
                'address_line1': '4 Morris spurs',
                'address_line2': '',
                'city': 'Jennaview',
                'postcode': 'L8 0NY',
                'recipient_email': '',
            },
            follow=True
        )

        self.assertOnPage(response, 'disbursements:pending_detail')

        patch_requests = [call.request for call in responses.calls if call.request.method == responses.PATCH]
        self.assertEqual(len(patch_requests), 1)
        self.assertJSONEqual(patch_requests[0].body.decode(), {
            'recipient_is_company': False,
            'recipient_first_name': new_recipient_first_name,
            'recipient_last_name': new_recipient_last_name,
        })

    @mock_pending_detail
    def test_update_remittance_description(self, calls_mocker):
        self.login(credentials={'username': 'test-hmp-brixton-a', 'password': 'pass'})

        # go to update page
        disbursement = SAMPLE_DISBURSEMENTS[3]
        calls_mocker(disbursement)
        self.prisoner_location_response(disbursement)

        response = self.client.get(
            reverse('disbursements:update_remittance_description', args=[disbursement['id']])
        )
        self.assertContains(response, disbursement['remittance_description'])
        self.assertNotContains(response, 'None given')

        responses.reset()

        # post update
        responses.add(
            responses.GET,
            api_url('/prisoner_locations/{prisoner_number}/'.format(
                prisoner_number=disbursement['prisoner_number']
            )),
            json={
                'prisoner_number': disbursement['prisoner_number'],
                'prisoner_dob': '1970-01-01',
                'prisoner_name': 'TEST QUASH2',
                'prison': 'BXI'
            },
            status=200,
        )
        responses.add(
            responses.PATCH,
            api_url('/disbursements/{pk}/'.format(pk=disbursement['id'])),
            status=200
        )

        new_remittance_description = 'LEGAL FEES'
        calls_mocker(disbursement)

        response = self.client.post(
            reverse('disbursements:update_remittance_description', args=[disbursement['id']]),
            data={
                'remittance': 'yes',
                'remittance_description': new_remittance_description,
            },
            follow=True
        )
        self.assertOnPage(response, 'disbursements:pending_detail')

        patch_requests = [call.request for call in responses.calls if call.request.method == responses.PATCH]
        self.assertEqual(len(patch_requests), 1)
        self.assertJSONEqual(patch_requests[0].body.decode(), {
            'remittance_description': new_remittance_description,
        })

    @mock_pending_detail
    def test_update_remittance_description_to_default(self, calls_mocker):
        self.login(credentials={'username': 'test-hmp-brixton-a', 'password': 'pass'})

        # go to update page
        disbursement = SAMPLE_DISBURSEMENTS[3]
        calls_mocker(disbursement)
        responses.add(
            responses.GET,
            api_url('/prisoner_locations/{prisoner_number}/'.format(
                prisoner_number=disbursement['prisoner_number']
            )),
            json={
                'prisoner_number': disbursement['prisoner_number'],
                'prisoner_dob': '1970-01-01',
                'prisoner_name': 'TEST QUASH2',
                'prison': 'BXI'
            },
            status=200,
        )

        response = self.client.get(
            reverse('disbursements:update_remittance_description', args=[disbursement['id']])
        )
        self.assertContains(response, disbursement['remittance_description'])
        self.assertNotContains(response, 'None given')

        responses.reset()

        # post update
        responses.add(
            responses.GET,
            api_url('/prisoner_locations/{prisoner_number}/'.format(
                prisoner_number=disbursement['prisoner_number']
            )),
            json={
                'prisoner_number': disbursement['prisoner_number'],
                'prisoner_dob': '1970-01-01',
                'prisoner_name': 'TEST QUASH2',
                'prison': 'BXI'
            },
            status=200,
        )
        responses.add(
            responses.PATCH,
            api_url('/disbursements/{pk}/'.format(pk=disbursement['id'])),
            status=200
        )

        # new_remittance_description = 'LEGAL FEES'
        calls_mocker(disbursement)

        response = self.client.post(
            reverse('disbursements:update_remittance_description', args=[disbursement['id']]),
            data={
                'remittance': 'no',
            },
            follow=True
        )
        self.assertOnPage(response, 'disbursements:pending_detail')

        patch_requests = [call.request for call in responses.calls if call.request.method == responses.PATCH]
        self.assertEqual(len(patch_requests), 1)
        self.assertJSONEqual(patch_requests[0].body.decode(), {
            'remittance_description': 'Payment from TEST QUASH2',
        })

    @mock_pending_detail
    def test_update_address(self, calls_mocker):
        self.login(credentials={'username': 'test-hmp-brixton-a', 'password': 'pass'})

        # go to update page
        disbursement = SAMPLE_DISBURSEMENTS[3]
        calls_mocker(disbursement)
        self.prisoner_location_response(disbursement)

        response = self.client.get(
            reverse('disbursements:update_recipient_address', args=[disbursement['id']])
        )
        self.assertOnPage(response, 'disbursements:update_recipient_address')
        # address picker shouldn't show on update
        self.assertNotContains(response, 'Choose address')
        self.assertNotContains(response, 'Or enter address manually')

        responses.reset()

        # post update
        responses.add(
            responses.PATCH,
            api_url('/disbursements/{pk}/'.format(pk=disbursement['id'])),
            status=200
        )

        new_address = {
            'address_line1': '54 Fake Road',
            'address_line2': '',
            'city': 'London',
            'postcode': 'n17 9xy'
        }
        updated_disbursement = dict(**disbursement)
        updated_disbursement.update(new_address)
        calls_mocker(updated_disbursement)
        self.prisoner_location_response(disbursement)

        response = self.client.post(
            reverse('disbursements:update_recipient_address', args=[updated_disbursement['id']]),
            data=new_address,
            follow=True
        )
        self.assertOnPage(response, 'disbursements:pending_detail')
        self.assertContains(response, new_address['address_line1'])
        self.assertContains(response, new_address['address_line2'])
        self.assertContains(response, new_address['city'])
        self.assertContains(response, new_address['postcode'])

    @mock_pending_detail
    def test_change_sending_method_to_bank_transfer_requests_account_details(self, calls_mocker):
        self.login(credentials={'username': 'test-hmp-brixton-a', 'password': 'pass'})

        # go to update sending method page
        disbursement = SAMPLE_DISBURSEMENTS[4]
        calls_mocker(disbursement)

        response = self.client.get(
            reverse('disbursements:update_sending_method', args=[disbursement['id']])
        )
        self.assertOnPage(response, 'disbursements:update_sending_method')

        responses.reset()

        # post sending method update
        calls_mocker(disbursement)
        responses.add(
            responses.GET,
            api_url('/prisoner_locations/{prisoner_number}/'.format(
                prisoner_number=disbursement['prisoner_number']
            )),
            json={
                'prisoner_number': disbursement['prisoner_number'],
                'prisoner_dob': '1970-01-01',
                'prisoner_name': 'JILLY HALL',
                'prison': 'BXI'
            },
            status=200,
        )
        response = self.client.post(
            reverse('disbursements:update_sending_method', args=[disbursement['id']]),
            data={'method': 'bank_transfer'}, follow=True
        )
        self.assertOnPage(response, 'disbursements:update_recipient_bank_account')

        responses.reset()

        # post bank account details
        calls_mocker(disbursement)
        responses.add(
            responses.GET,
            api_url('/prisoner_locations/{prisoner_number}/'.format(
                prisoner_number=disbursement['prisoner_number']
            )),
            json={
                'prisoner_number': disbursement['prisoner_number'],
                'prisoner_dob': '1970-01-01',
                'prisoner_name': 'JILLY HALL',
                'prison': 'BXI'
            },
            status=200,
        )
        responses.add(
            responses.PATCH,
            api_url('/disbursements/{pk}/'.format(pk=disbursement['id'])),
            status=200
        )
        response = self.client.post(
            reverse(
                'disbursements:update_recipient_bank_account',
                args=[disbursement['id']]
            ),
            data={'account_number': '11111111', 'sort_code': '11-11-11'},
            follow=True
        )
        self.assertOnPage(response, 'disbursements:pending_detail')


class ConfirmPendingDisbursementTestCase(PendingDisbursementTestCase):

    def url(self, pk):
        return reverse('disbursements:pending_detail', args=[pk])

    @mock_pending_detail
    @mock.patch(
        'disbursements.views.nomis.create_transaction',
        return_value={'id': '12345-1'},
    )
    def test_confirm_disbursement(self, calls_mocker, mock_nomis_create_transaction):
        self.login(credentials={'username': 'test-hmp-brixton-a', 'password': 'pass'})

        disbursement = SAMPLE_DISBURSEMENTS[4]
        calls_mocker(disbursement)
        responses.add(
            responses.POST,
            api_url('/disbursements/actions/preconfirm/'),
            status=200
        )
        responses.add(
            responses.POST,
            api_url('/disbursements/actions/confirm/'),
            status=200
        )

        response = self.client.post(self.url(disbursement['id']), data={'confirmation': 'yes'}, follow=True)
        self.assertOnPage(response, 'disbursements:confirmed')
        self.assertContains(response, '12345-1')

        mock_nomis_create_transaction.assert_called_once_with(
            prison_id='BXI',
            prisoner_number='A1448AE',
            amount=3000,
            record_id='d660',
            description='Sent to Katy Hicks',
            transaction_type='RELA',
            retries=1,
        )

    @mock_pending_detail
    @mock.patch(
        'disbursements.views.nomis.create_transaction',
        side_effect=HTTPError(response=mock.Mock(status_code=500)),
    )
    def test_confirm_disbursement_resets_on_failure(self, calls_mocker, _):
        self.login(credentials={'username': 'test-hmp-brixton-a', 'password': 'pass'})

        disbursement = SAMPLE_DISBURSEMENTS[4]
        calls_mocker(disbursement)
        responses.add(
            responses.POST,
            api_url('/disbursements/actions/preconfirm/'),
            status=200
        )
        responses.add(
            responses.POST,
            api_url('/disbursements/actions/reset/'),
            status=200
        )

        with silence_logger():
            response = self.client.post(self.url(disbursement['id']), data={'confirmation': 'yes'}, follow=True)
        self.assertOnPage(response, 'disbursements:pending_detail')
        self.assertContains(response, 'Payment not confirmed due to technical error')


class RejectPendingDisbursementTestCase(PendingDisbursementTestCase):

    def url(self, pk):
        return reverse('disbursements:pending_reject', args=[pk])

    @mock_pending_list
    def test_reject_disbursement(self, calls_mocker):
        self.login(credentials={'username': 'test-hmp-brixton-a', 'password': 'pass'})

        disbursement = SAMPLE_DISBURSEMENTS[4]
        responses.add(
            responses.POST,
            api_url('/disbursements/comments/'),
            status=201
        )
        responses.add(
            responses.POST,
            api_url('/disbursements/actions/reject/'),
            status=200
        )
        calls_mocker(disbursements=SAMPLE_DISBURSEMENTS[:3])

        response = self.client.post(
            self.url(disbursement['id']), data={'reason': 'bad one'}, follow=True
        )
        self.assertOnPage(response, 'disbursements:pending_list')
        self.assertContains(response, 'Payment request cancelled.')
