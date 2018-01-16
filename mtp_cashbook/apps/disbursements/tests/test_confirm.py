from django.test import override_settings
from django.urls import reverse
import responses

from cashbook.tests import (
    MTPBaseTestCase, api_url, nomis_url, override_nomis_settings
)

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
        'recipient_first_name': 'Geoffrey',
        'recipient_last_name': 'Jennings',
        'address_line1': '632 Shane stravenue',
        'address_line2': None,
        'city': 'Lake Louisville',
        'postcode': 'N2K 9FX',
        'country': 'UK',
        'recipient_email': 'Geoffrey.Jennings@mail.local',
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
        'recipient_first_name': 'Angela',
        'recipient_last_name': 'Wood',
        'address_line1': 'Flat 66x',
        'address_line2': 'Nolan grove',
        'city': 'Alexanderbury',
        'postcode': 'N21 7SS',
        'country': 'UK',
        'recipient_email': 'Angela.Wood@mail.local',
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
        'recipient_first_name': 'Jessica',
        'recipient_last_name': 'Hill',
        'address_line1': 'Flat 6',
        'address_line2': 'Carpenter manor',
        'city': 'North Marcusfort',
        'postcode': 'IM0M 2TJ',
        'country': 'UK',
        'recipient_email': None,
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
        'recipient_first_name': 'Ross',
        'recipient_last_name': 'Johnson',
        'address_line1': '460 Johnson springs',
        'address_line2': None,
        'city': 'South Georgia',
        'postcode': 'E09 5SP',
        'country': 'UK',
        'recipient_email': 'Ross.Johnson@mail.local',
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
        'recipient_first_name': 'Katy',
        'recipient_last_name': 'Hicks',
        'address_line1': '4 Morris spurs',
        'address_line2': None,
        'city': 'Jennaview',
        'postcode': 'L8 0NY',
        'country': 'UK',
        'recipient_email': 'Katy.Hicks@mail.local',
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
    }
]


class PendingDisbursementTestCase(MTPBaseTestCase):

    def add_nomis_responses_for_disbursement(self, disbursement):
        if disbursement['prisoner_name'] == 'PRISONER MOVED':
            responses.add(
                responses.GET,
                nomis_url('/prison/{nomis_id}/offenders/{prisoner_number}/accounts/'.format(
                    nomis_id=disbursement['prison'],
                    prisoner_number=disbursement['prisoner_number']
                )),
                status=500
            )
        else:
            responses.add(
                responses.GET,
                nomis_url('/prison/{nomis_id}/offenders/{prisoner_number}/accounts/'.format(
                    nomis_id=disbursement['prison'],
                    prisoner_number=disbursement['prisoner_number']
                )),
                json={
                    'cash': 10000,
                    'spends': 2000,
                    'savings': 10000
                },
                status=200
            )

        responses.add(
            responses.GET,
            nomis_url('/offenders/{prisoner_number}/location/'.format(
                prisoner_number=disbursement['prisoner_number']
            )),
            json={'establishment': {
                'code': (
                    'LEI' if disbursement['prisoner_name'] == 'PRISONER MOVED'
                    else disbursement['prison']
                ),
                'desc': 'HMP'
            }},
            status=200
        )

    def pending_list(self, disbursements=SAMPLE_DISBURSEMENTS):
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

        for disbursement in disbursements:
            self.add_nomis_responses_for_disbursement(disbursement)

    def pending_detail(self, disbursement):
        responses.add(
            responses.GET,
            api_url('/disbursements/{pk}/'.format(pk=disbursement['id'])),
            json=disbursement,
            status=200
        )

        self.add_nomis_responses_for_disbursement(disbursement)


class PendingListDisbursementTestCase(PendingDisbursementTestCase):

    @property
    def url(self):
        return reverse('disbursements:pending_list')

    @responses.activate
    @override_nomis_settings
    @override_settings(DISBURSEMENT_PRISONS=['BXI'])
    def test_display_pending_disbursements(self):
        self.login(credentials={'username': 'test-hmp-brixton-a', 'password': 'pass'})
        self.pending_list(disbursements=[SAMPLE_DISBURSEMENTS[3], SAMPLE_DISBURSEMENTS[4]])

        response = self.client.get(self.url)
        self.assertOnPage(response, 'disbursements:pending_list')

        self.assertContains(response, 'Confirmation required')

    @responses.activate
    @override_nomis_settings
    @override_settings(DISBURSEMENT_PRISONS=['BXI'])
    def test_pending_list_self_own(self):
        self.login(credentials={'username': 'test-hmp-brixton-a', 'password': 'pass'})
        self.pending_list(disbursements=[SAMPLE_DISBURSEMENTS[0]])

        response = self.client.get(self.url)
        self.assertOnPage(response, 'disbursements:pending_list')

        self.assertContains(response, 'Another colleague needs to confirm this payment')

    @responses.activate
    @override_nomis_settings
    @override_settings(DISBURSEMENT_PRISONS=['BXI'])
    def test_pending_list_prisoner_moved(self):
        self.login(credentials={'username': 'test-hmp-brixton-a', 'password': 'pass'})
        self.pending_list(disbursements=[SAMPLE_DISBURSEMENTS[1]])

        response = self.client.get(self.url)
        self.assertOnPage(response, 'disbursements:pending_list')

        self.assertContains(response, 'Prisoner no longer in  this prison')

    @responses.activate
    @override_nomis_settings
    @override_settings(DISBURSEMENT_PRISONS=['BXI'])
    def test_pending_list_with_insufficient_funds(self):
        self.login(credentials={'username': 'test-hmp-brixton-a', 'password': 'pass'})
        self.pending_list(disbursements=[SAMPLE_DISBURSEMENTS[2]])

        response = self.client.get(self.url)
        self.assertOnPage(response, 'disbursements:pending_list')

        self.assertContains(response, 'Insufficient funds')


class PendingDetailDisbursementTestCase(PendingDisbursementTestCase):

    def url(self, pk):
        return reverse('disbursements:pending_detail', args=[pk])

    @responses.activate
    @override_nomis_settings
    @override_settings(DISBURSEMENT_PRISONS=['BXI'])
    def test_valid_pending_disbursement(self):
        self.login(credentials={'username': 'test-hmp-brixton-a', 'password': 'pass'})
        disbursement = SAMPLE_DISBURSEMENTS[3]
        self.pending_detail(disbursement=disbursement)

        response = self.client.get(self.url(disbursement['id']))
        self.assertOnPage(response, 'disbursements:pending_detail')
        self.assertContains(response, 'Confirm payment')

    @responses.activate
    @override_nomis_settings
    @override_settings(DISBURSEMENT_PRISONS=['BXI'])
    def test_insufficient_funds_pending_disbursement(self):
        self.login(credentials={'username': 'test-hmp-brixton-a', 'password': 'pass'})
        disbursement = SAMPLE_DISBURSEMENTS[2]
        self.pending_detail(disbursement=disbursement)

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

    @responses.activate
    @override_nomis_settings
    @override_settings(DISBURSEMENT_PRISONS=['BXI'])
    def test_update_prisoner(self):
        self.login(credentials={'username': 'test-hmp-brixton-a', 'password': 'pass'})

        # go to update page
        disbursement = SAMPLE_DISBURSEMENTS[3]
        self.pending_detail(disbursement=disbursement)
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
        self.pending_detail(disbursement=updated_disbursement)

        response = self.client.post(
            reverse('disbursements:update_prisoner', args=[updated_disbursement['id']]),
            data={'prisoner_number': new_prisoner_number}, follow=True
        )
        self.assertOnPage(response, 'disbursements:pending_detail')
        self.assertContains(response, new_prisoner_number)

    @responses.activate
    @override_nomis_settings
    @override_settings(DISBURSEMENT_PRISONS=['BXI'])
    def test_change_sending_method_to_bank_transfer_requests_account_details(self):
        self.login(credentials={'username': 'test-hmp-brixton-a', 'password': 'pass'})

        # go to update sending method page
        disbursement = SAMPLE_DISBURSEMENTS[4]
        self.pending_detail(disbursement=disbursement)

        response = self.client.get(
            reverse('disbursements:update_sending_method', args=[disbursement['id']])
        )
        self.assertOnPage(response, 'disbursements:update_sending_method')

        responses.reset()

        # post sending method update
        self.pending_detail(disbursement=disbursement)
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
        self.pending_detail(disbursement=disbursement)
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
        return reverse('disbursements:pending_confirm', args=[pk])

    @responses.activate
    @override_nomis_settings
    @override_settings(DISBURSEMENT_PRISONS=['BXI'])
    def test_confirm_disbursement(self):
        self.login(credentials={'username': 'test-hmp-brixton-a', 'password': 'pass'})

        disbursement = SAMPLE_DISBURSEMENTS[4]
        self.pending_detail(disbursement=disbursement)
        responses.add(
            responses.POST,
            api_url('/disbursements/actions/preconfirm/'),
            status=200
        )
        responses.add(
            responses.POST,
            nomis_url('/prison/{nomis_id}/offenders/{prisoner_number}/transactions/'.format(
                nomis_id=disbursement['prison'],
                prisoner_number=disbursement['prisoner_number']
            )),
            json={'id': '12345-1'},
            status=200
        )
        responses.add(
            responses.POST,
            api_url('/disbursements/actions/confirm/'),
            status=200
        )

        response = self.client.post(self.url(disbursement['id']), follow=True)
        self.assertOnPage(response, 'disbursements:pending_confirm')
        self.assertContains(response, '12345-1')

    @responses.activate
    @override_nomis_settings
    @override_settings(DISBURSEMENT_PRISONS=['BXI'])
    def test_confirm_disbursement_resets_on_failure(self):
        self.login(credentials={'username': 'test-hmp-brixton-a', 'password': 'pass'})

        disbursement = SAMPLE_DISBURSEMENTS[4]
        self.pending_detail(disbursement=disbursement)
        responses.add(
            responses.POST,
            api_url('/disbursements/actions/preconfirm/'),
            status=200
        )
        responses.add(
            responses.POST,
            nomis_url('/prison/{nomis_id}/offenders/{prisoner_number}/transactions/'.format(
                nomis_id=disbursement['prison'],
                prisoner_number=disbursement['prisoner_number']
            )),
            status=500
        )
        responses.add(
            responses.POST,
            api_url('/disbursements/actions/reset/'),
            status=200
        )

        response = self.client.post(self.url(disbursement['id']), follow=True)
        self.assertOnPage(response, 'disbursements:pending_detail')


class RejectPendingDisbursementTestCase(PendingDisbursementTestCase):

    def url(self, pk):
        return reverse('disbursements:pending_reject', args=[pk])

    @responses.activate
    @override_nomis_settings
    @override_settings(DISBURSEMENT_PRISONS=['BXI'])
    def test_reject_disbursement(self):
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
        self.pending_list(disbursements=SAMPLE_DISBURSEMENTS[:3])

        response = self.client.post(
            self.url(disbursement['id']), data={'reason': 'bad one'}, follow=True
        )
        self.assertOnPage(response, 'disbursements:pending_list')
        self.assertContains(response, 'Payment request cancelled.')
