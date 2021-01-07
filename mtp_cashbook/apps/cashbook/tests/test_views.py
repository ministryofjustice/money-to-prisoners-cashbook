import json
from datetime import datetime
from unittest import mock
import logging

from django.core import mail
from django.test import override_settings
from django.urls import reverse
from mtp_common.test_utils import silence_logger
from requests.exceptions import HTTPError
import responses

from cashbook.tests import (
    api_url,
    MTPBaseTestCase,
    wrap_response_data,
)

CREDIT_1 = {
    'id': 1,
    'prisoner_name': 'John Smith',
    'prisoner_number': 'A1234BC',
    'prison': 'BXI',
    'amount': 5200,
    'sender_name': 'Fred Smith',
    'sender_email': 'fred.smith@mail.local',
    'short_ref_number': '89AF76GH',
    'received_at': '2017-01-25T12:00:00Z',
    'owner': 100,
    'owner_name': 'Staff 1',
    'set_manual_at': '2017-01-26T12:00:00Z',
}
CREDIT_2 = {
    'id': 2,
    'prisoner_name': 'John Jones',
    'prisoner_number': 'A1234GG',
    'prison': 'BXI',
    'amount': 4500,
    'sender_name': 'Fred Jones',
    'sender_email': 'fred.jones@mail.local',
    'short_ref_number': '98KI32SA',
    'received_at': '2017-01-25T12:00:00Z',
    'owner': 100,
    'owner_name': 'Staff 1',
    'set_manual_at': '2017-01-26T12:00:00Z',
}
PROCESSING_BATCH = {
    'id': 10,
    'user': 1,
    'credits': [1, 2],
    'created': datetime.now().isoformat(),
    'expired': False
}
EXPIRED_PROCESSING_BATCH = {
    'id': 10,
    'user': 1,
    'credits': [1, 2],
    'created': datetime.now().isoformat(),
    'expired': True
}


@override_settings(PRISONER_CAPPING_ENABLED=False)
class NewCreditsViewTestCase(MTPBaseTestCase):

    @property
    def url(self):
        return reverse('new-credits')

    def test_new_credits_display(self):
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.GET,
                api_url('/credits/batches/'),
                json=wrap_response_data(),
                status=200,
            )
            # get new credits
            rsps.add(
                rsps.GET,
                api_url('/credits/?ordering=-received_at&offset=0&limit=100&status=credit_pending&resolution=pending'),
                json=wrap_response_data(CREDIT_1, CREDIT_2),
                status=200,
                match_querystring=True,
            )
            # get manual credits
            rsps.add(
                rsps.GET,
                api_url('/credits/?resolution=manual&status=credit_pending&offset=0&limit=100&ordering=-received_at'),
                json=wrap_response_data(),
                status=200,
                match_querystring=True,
            )
            self.login()
            response = self.client.get(self.url, follow=True)
            self.assertContains(response, '52.00')
            self.assertContains(response, '45.00')

    @override_settings(ENVIRONMENT='prod')  # because non-prod environments don't send to .local
    @mock.patch(
        'cashbook.tasks.nomis.create_transaction',

        # return {'id' == '<prisoner-number>-1'}
        side_effect=lambda **kwargs: {'id': f'{kwargs["prisoner_number"]}-1'},
    )
    def test_new_credits_submit(self, mock_create_transaction):
        with responses.RequestsMock() as rsps:
            # get new credits
            rsps.add(
                rsps.GET,
                api_url('/credits/?ordering=-received_at&offset=0&limit=100&status=credit_pending&resolution=pending'),
                json=wrap_response_data(CREDIT_1, CREDIT_2),
                status=200,
                match_querystring=True,
            )
            # get manual credits
            rsps.add(
                rsps.GET,
                api_url('/credits/?resolution=manual&status=credit_pending&offset=0&limit=100&ordering=-received_at'),
                json=wrap_response_data(),
                status=200,
                match_querystring=True,
            )
            # create batch
            rsps.add(
                rsps.POST,
                api_url('/credits/batches/'),
                status=201,
            )
            rsps.add(
                rsps.POST,
                api_url('/credits/actions/credit/'),
                status=204,
            )
            rsps.add(
                rsps.POST,
                api_url('/credits/actions/credit/'),
                status=204,
            )
            # REDIRECT after success
            # get active batches
            rsps.add(
                rsps.GET,
                api_url('/credits/batches/'),
                json=wrap_response_data(PROCESSING_BATCH),
                status=200,
            )
            # get incomplete credits
            rsps.add(
                rsps.GET,
                api_url('/credits/?resolution=pending&pk=1&pk=2'),
                json=wrap_response_data(),
                status=200,
                match_querystring=True,
            )
            # get complete credits
            rsps.add(
                rsps.GET,
                api_url('/credits/?resolution=credited&pk=1&pk=2'),
                json=wrap_response_data(CREDIT_1, CREDIT_2),
                status=200,
                match_querystring=True,
            )
            # delete completed batch
            rsps.add(
                rsps.DELETE,
                api_url('/credits/batches/%s/' % PROCESSING_BATCH['id']),
                status=200,
            )
            # get new credits
            rsps.add(
                rsps.GET,
                api_url('/credits/?ordering=-received_at&offset=0&limit=100&status=credit_pending&resolution=pending'),
                json=wrap_response_data(),
                status=200,
                match_querystring=True,
            )
            # get manual credits
            rsps.add(
                rsps.GET,
                api_url('/credits/?resolution=manual&status=credit_pending&offset=0&limit=100&ordering=-received_at'),
                json=wrap_response_data(),
                status=200,
                match_querystring=True,
            )

            self.login()
            response = self.client.post(
                self.url,
                data={'credits': [1, 2], 'submit_new': 'submit'},
                follow=True
            )
            self.assertEqual(response.status_code, 200)
            expected_calls = [
                [{'id': 1, 'credited': True, 'nomis_transaction_id': 'A1234BC-1'}],
                [{'id': 2, 'credited': True, 'nomis_transaction_id': 'A1234GG-1'}]
            ]
            self.assertTrue(
                json.loads(rsps.calls[3].request.body.decode('utf-8')) in expected_calls and
                json.loads(rsps.calls[4].request.body.decode('utf-8')) in expected_calls
            )

            request_nomis_session_used = mock_create_transaction.call_args_list[0][1]['session']
            mock_create_transaction.assert_has_calls(
                [
                    mock.call(
                        amount=5200,
                        description='Sent by Fred Smith',
                        prison_id='BXI',
                        prisoner_number='A1234BC',
                        record_id='1',
                        retries=1,
                        session=request_nomis_session_used,
                        transaction_type='MTDS',
                    ),
                    mock.call(
                        amount=4500,
                        description='Sent by Fred Jones',
                        prison_id='BXI',
                        prisoner_number='A1234GG',
                        record_id='2',
                        retries=1,
                        session=request_nomis_session_used,
                        transaction_type='MTDS',
                    ),
                ],
                any_order=True,
            )
            self.assertContains(response, '2 credits sent to NOMIS')
            self.assertEqual(len(mail.outbox), 2)
            self.assertTrue(
                '£52.00' in mail.outbox[0].body and '£45.00' in mail.outbox[1].body or
                '£52.00' in mail.outbox[1].body and '£45.00' in mail.outbox[0].body
            )

    @override_settings(
        ENVIRONMENT='prod',  # because non-prod environments don't send to .local
        PRISONER_CAPPING_ENABLED=True,
        PRISONER_CAPPING_THRESHOLD_IN_POUNDS=100,
    )
    @mock.patch('cashbook.tasks.logger')
    @mock.patch('cashbook.tasks.nomis')
    def test_balance_check_after_credit(self, mock_nomis, mock_logger):
        balances = {
            # credit 1 – £52 – within cap
            'A1234BC': {'cash': 800, 'spends': 0, 'savings': 4000},
            # credit 2 – £45 – exceeds cap
            'A1234GG': {'cash': 1000, 'spends': 200, 'savings': 5500},
        }

        def create_transaction(**kwargs):
            prisoner_number = kwargs['prisoner_number']
            amount = kwargs['amount']
            balances[prisoner_number]['cash'] += amount
            return {'id': f'{prisoner_number}-1'}

        def get_account_balances(prison, prisoner_number):
            self.assertEqual(prison, 'BXI', msg='Unexpected test data')
            return balances[prisoner_number]

        mock_nomis.create_transaction = create_transaction
        mock_nomis.get_account_balances = get_account_balances

        with responses.RequestsMock() as rsps:
            # get new credits
            rsps.add(
                rsps.GET,
                api_url('/credits/?ordering=-received_at&offset=0&limit=100&status=credit_pending&resolution=pending'),
                json=wrap_response_data(CREDIT_1, CREDIT_2),
                status=200,
                match_querystring=True,
            )
            # get manual credits
            rsps.add(
                rsps.GET,
                api_url('/credits/?resolution=manual&status=credit_pending&offset=0&limit=100&ordering=-received_at'),
                json=wrap_response_data(),
                status=200,
                match_querystring=True,
            )
            # create batch
            rsps.add(
                rsps.POST,
                api_url('/credits/batches/'),
                status=201,
            )
            rsps.add(
                rsps.POST,
                api_url('/credits/actions/credit/'),
                status=204,
            )
            rsps.add(
                rsps.POST,
                api_url('/credits/actions/credit/'),
                status=204,
            )
            # REDIRECT after success
            # get active batches
            rsps.add(
                rsps.GET,
                api_url('/credits/batches/'),
                json=wrap_response_data(PROCESSING_BATCH),
                status=200,
            )
            # get incomplete credits
            rsps.add(
                rsps.GET,
                api_url('/credits/?resolution=pending&pk=1&pk=2'),
                json=wrap_response_data(),
                status=200,
                match_querystring=True,
            )
            # get complete credits
            rsps.add(
                rsps.GET,
                api_url('/credits/?resolution=credited&pk=1&pk=2'),
                json=wrap_response_data(CREDIT_1, CREDIT_2),
                status=200,
                match_querystring=True,
            )
            # delete completed batch
            rsps.add(
                rsps.DELETE,
                api_url('/credits/batches/%s/' % PROCESSING_BATCH['id']),
                status=200,
            )
            # get new credits
            rsps.add(
                rsps.GET,
                api_url('/credits/?ordering=-received_at&offset=0&limit=100&status=credit_pending&resolution=pending'),
                json=wrap_response_data(),
                status=200,
                match_querystring=True,
            )
            # get manual credits
            rsps.add(
                rsps.GET,
                api_url('/credits/?resolution=manual&status=credit_pending&offset=0&limit=100&ordering=-received_at'),
                json=wrap_response_data(),
                status=200,
                match_querystring=True,
            )

            self.login()
            response = self.client.post(
                self.url,
                data={'credits': [1, 2], 'submit_new': 'submit'},
                follow=True
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '2 credits sent to NOMIS')
        logger_error_messages = [call[0][0] for call in mock_logger.error.call_args_list]
        self.assertEqual(len(logger_error_messages), 1)
        self.assertEqual(logger_error_messages[0], 'NOMIS account balance for A1234GG exceeds cap')

    @override_settings(ENVIRONMENT='prod')  # because non-prod environments don't send to .local
    @mock.patch(
        'cashbook.tasks.nomis.create_transaction',
        side_effect=[
            HTTPError(response=mock.Mock(status_code=409)),
            {'id': 'A1234GG-1'},
        ],
    )
    def test_new_credits_submit_with_conflict(self, _):
        with responses.RequestsMock() as rsps:
            # get new credits
            rsps.add(
                rsps.GET,
                api_url('/credits/?ordering=-received_at&offset=0&limit=100&status=credit_pending&resolution=pending'),
                json=wrap_response_data(CREDIT_1, CREDIT_2),
                status=200,
                match_querystring=True,
            )
            # get manual credits
            rsps.add(
                rsps.GET,
                api_url('/credits/?resolution=manual&status=credit_pending&offset=0&limit=100&ordering=-received_at'),
                json=wrap_response_data(),
                status=200,
                match_querystring=True,
            )
            # create batch
            rsps.add(
                rsps.POST,
                api_url('/credits/batches/'),
                status=201,
            )
            rsps.add(
                rsps.POST,
                api_url('/credits/actions/credit/'),
                status=204,
            )
            rsps.add(
                rsps.POST,
                api_url('/credits/actions/credit/'),
                status=204,
            )
            # REDIRECT after success
            # get active batches
            rsps.add(
                rsps.GET,
                api_url('/credits/batches/'),
                json=wrap_response_data(PROCESSING_BATCH),
                status=200,
            )
            # get incomplete credits
            rsps.add(
                rsps.GET,
                api_url('/credits/?resolution=pending&pk=1&pk=2'),
                json=wrap_response_data(),
                status=200,
                match_querystring=True,
            )
            # get complete credits
            rsps.add(
                rsps.GET,
                api_url('/credits/?resolution=credited&pk=1&pk=2'),
                json=wrap_response_data(CREDIT_1, CREDIT_2),
                status=200,
                match_querystring=True,
            )
            # delete completed batch
            rsps.add(
                rsps.DELETE,
                api_url('/credits/batches/%s/' % PROCESSING_BATCH['id']),
                status=200,
            )
            # get new credits
            rsps.add(
                rsps.GET,
                api_url('/credits/?ordering=-received_at&offset=0&limit=100&status=credit_pending&resolution=pending'),
                json=wrap_response_data(),
                status=200,
                match_querystring=True,
            )
            # get manual credits
            rsps.add(
                rsps.GET,
                api_url('/credits/?resolution=manual&status=credit_pending&offset=0&limit=100&ordering=-received_at'),
                json=wrap_response_data(),
                status=200,
                match_querystring=True,
            )

            self.login()
            with silence_logger(name='mtp', level=logging.ERROR):
                response = self.client.post(
                    self.url,
                    data={'credits': [1, 2], 'submit_new': 'submit'},
                    follow=True
                )
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, '2 credits sent to NOMIS')
            self.assertEqual(len(mail.outbox), 2)

    @override_settings(ENVIRONMENT='prod')  # because non-prod environments don't send to .local
    @mock.patch(
        'cashbook.tasks.nomis.create_transaction',
        side_effect=[
            HTTPError(response=mock.Mock(status_code=400)),
            {'id': 'A1234GG-1'},
        ],
    )
    @mock.patch(
        'cashbook.tasks.nomis.get_location',
        return_value={
            'nomis_id': 'LEI',
            'name': 'LEEDS (HMP)',
        },
    )
    def test_new_credits_submit_with_uncreditable(self, *_):
        with responses.RequestsMock() as rsps:
            # get new credits
            rsps.add(
                rsps.GET,
                api_url('/credits/?ordering=-received_at&offset=0&limit=100&status=credit_pending&resolution=pending'),
                json=wrap_response_data(CREDIT_1, CREDIT_2),
                status=200,
                match_querystring=True,
            )
            # get manual credits
            rsps.add(
                rsps.GET,
                api_url('/credits/?resolution=manual&status=credit_pending&offset=0&limit=100&ordering=-received_at'),
                json=wrap_response_data(),
                status=200,
                match_querystring=True,
            )
            # create batch
            rsps.add(
                rsps.POST,
                api_url('/credits/batches/'),
                status=201,
            )
            # credit credits to NOMIS and API
            rsps.add(
                rsps.POST,
                api_url('/credits/actions/setmanual/'),
                status=204,
            )
            rsps.add(
                rsps.POST,
                api_url('/credits/actions/credit/'),
                status=204,
            )
            # REDIRECT after success
            # get active batches
            rsps.add(
                rsps.GET,
                api_url('/credits/batches/'),
                json=wrap_response_data(PROCESSING_BATCH),
                status=200,
            )
            # get incomplete credits
            rsps.add(
                rsps.GET,
                api_url('/credits/?resolution=pending&pk=1&pk=2'),
                json=wrap_response_data(),
                status=200,
                match_querystring=True,
            )
            # get complete credits
            rsps.add(
                rsps.GET,
                api_url('/credits/?resolution=credited&pk=1&pk=2'),
                json=wrap_response_data(CREDIT_2),
                status=200,
                match_querystring=True,
            )
            # delete completed batch
            rsps.add(
                rsps.DELETE,
                api_url('/credits/batches/%s/' % PROCESSING_BATCH['id']),
                status=200,
            )
            # get new credits
            rsps.add(
                rsps.GET,
                api_url('/credits/?ordering=-received_at&offset=0&limit=100&status=credit_pending&resolution=pending'),
                json=wrap_response_data(),
                status=200,
                match_querystring=True,
            )
            # get manual credits
            rsps.add(
                rsps.GET,
                api_url('/credits/?resolution=manual&status=credit_pending&offset=0&limit=100&ordering=-received_at'),
                json=wrap_response_data(CREDIT_1),
                status=200,
                match_querystring=True,
            )

            self.login()
            with silence_logger(name='mtp', level=logging.CRITICAL):
                response = self.client.post(
                    self.url,
                    data={'credits': [1, 2], 'submit_new': 'submit'},
                    follow=True
                )
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, '1 credit sent to NOMIS')
            self.assertContains(response, '1 credit needs your manual input in NOMIS')
            self.assertEqual(len(mail.outbox), 1)

    @override_settings(ENVIRONMENT='prod')  # because non-prod environments don't send to .local
    @mock.patch(
        'cashbook.views.nomis.get_location',
        return_value={
            'nomis_id': 'LEI',
            'name': 'LEEDS (HMP)',
        },
    )
    def test_manual_credits_submit(self, _):
        with responses.RequestsMock() as rsps:
            # get new credits
            rsps.add(
                rsps.GET,
                api_url('/credits/?ordering=-received_at&offset=0&limit=100&status=credit_pending&resolution=pending'),
                json=wrap_response_data(),
                status=200,
                match_querystring=True,
            )
            # get manual credits
            rsps.add(
                rsps.GET,
                api_url('/credits/?resolution=manual&status=credit_pending&offset=0&limit=100&ordering=-received_at'),
                json=wrap_response_data(CREDIT_1, CREDIT_2),
                status=200,
                match_querystring=True,
            )
            # credit credit to API
            rsps.add(
                rsps.POST,
                api_url('/credits/actions/credit/'),
                status=204,
            )
            # REDIRECT after success
            # get active batches
            rsps.add(
                rsps.GET,
                api_url('/credits/batches/'),
                json=wrap_response_data(),
                status=200,
            )
            # get new credits
            rsps.add(
                rsps.GET,
                api_url('/credits/?ordering=-received_at&offset=0&limit=100&status=credit_pending&resolution=pending'),
                json=wrap_response_data(),
                status=200,
                match_querystring=True,
            )
            # get manual credits
            rsps.add(
                rsps.GET,
                api_url('/credits/?resolution=manual&status=credit_pending&offset=0&limit=100&ordering=-received_at'),
                json=wrap_response_data(CREDIT_2),
                status=200,
                match_querystring=True,
            )

            self.login()
            response = self.client.post(
                self.url,
                data={'submit_manual_1': ''},
                follow=True
            )
            self.assertEqual(
                json.loads(rsps.calls[2].request.body.decode('utf-8')),
                [{'id': 1, 'credited': True}]
            )
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, '1 credit manually input by you into NOMIS')


@mock.patch(
    'cashbook.views.nomis.get_location',
    mock.Mock(
        return_value={
            'nomis_id': 'LEI',
            'name': 'LEEDS (HMP)',
        },
    ),
)
class ProcessingCreditsViewTestCase(MTPBaseTestCase):

    @property
    def url(self):
        return reverse('processing-credits')

    def test_new_credits_redirects_to_processing_when_batch_active(self):
        with responses.RequestsMock() as rsps:
            # get active batches
            rsps.add(
                rsps.GET,
                api_url('/credits/batches/'),
                json=wrap_response_data(PROCESSING_BATCH),
                status=200,
            )
            # get incomplete credits
            rsps.add(
                rsps.GET,
                api_url('/credits/?resolution=pending&pk=1&pk=2'),
                json=wrap_response_data(CREDIT_1, CREDIT_2),
                status=200,
                match_querystring=True,
            )
            # get active batches
            rsps.add(
                rsps.GET,
                api_url('/credits/batches/'),
                json=wrap_response_data(PROCESSING_BATCH),
                status=200,
            )
            # get incomplete credits
            rsps.add(
                rsps.GET,
                api_url('/credits/?resolution=pending&pk=1&pk=2'),
                json=wrap_response_data(CREDIT_1, CREDIT_2),
                status=200,
                match_querystring=True,
            )

            self.login()
            response = self.client.get(reverse('new-credits'), follow=True)
            self.assertRedirects(response, self.url)

    def test_processing_credits_displays_percentage(self):
        with responses.RequestsMock() as rsps:
            # get active batches
            rsps.add(
                rsps.GET,
                api_url('/credits/batches/'),
                json=wrap_response_data(PROCESSING_BATCH),
                status=200,
            )
            # get incomplete credits
            rsps.add(
                rsps.GET,
                api_url('/credits/?resolution=pending&pk=1&pk=2'),
                json=wrap_response_data(CREDIT_2),
                status=200,
                match_querystring=True,
            )

            self.login()
            response = self.client.get(reverse('processing-credits'), follow=True)
            self.assertContains(response, '50%')

    def test_processing_credits_displays_continue_when_done(self):
        with responses.RequestsMock() as rsps:
            # get active batches
            rsps.add(
                rsps.GET,
                api_url('/credits/batches/'),
                json=wrap_response_data(PROCESSING_BATCH),
                status=200,
            )
            # get incomplete credits
            rsps.add(
                rsps.GET,
                api_url('/credits/?resolution=pending&pk=1&pk=2'),
                json=wrap_response_data(),
                status=200,
                match_querystring=True,
            )

            self.login()
            response = self.client.get(reverse('processing-credits'), follow=True)
            self.assertContains(response, 'Continue')

    def test_processing_credits_redirects_to_new_for_expired_batch(self):
        with responses.RequestsMock() as rsps:
            # get active batches
            rsps.add(
                rsps.GET,
                api_url('/credits/batches/'),
                json=wrap_response_data(EXPIRED_PROCESSING_BATCH),
                status=200,
            )
            # get active batches
            rsps.add(
                rsps.GET,
                api_url('/credits/batches/'),
                json=wrap_response_data(EXPIRED_PROCESSING_BATCH),
                status=200,
            )
            # get incomplete credits
            rsps.add(
                rsps.GET,
                api_url('/credits/?resolution=pending&pk=1&pk=2'),
                json=wrap_response_data(CREDIT_2),
                status=200,
                match_querystring=True,
            )
            # get complete credits
            rsps.add(
                rsps.GET,
                api_url('/credits/?resolution=credited&pk=1&pk=2'),
                json=wrap_response_data(CREDIT_1),
                status=200,
                match_querystring=True,
            )
            rsps.add(
                rsps.DELETE,
                api_url('/credits/batches/%s/' % PROCESSING_BATCH['id']),
                status=200,
            )
            # get new credits
            rsps.add(
                rsps.GET,
                api_url('/credits/?ordering=-received_at&offset=0&limit=100&status=credit_pending&resolution=pending'),
                json=wrap_response_data(),
                status=200,
                match_querystring=True,
            )
            # get manual credits
            rsps.add(
                rsps.GET,
                api_url('/credits/?resolution=manual&status=credit_pending&offset=0&limit=100&ordering=-received_at'),
                json=wrap_response_data(CREDIT_2),
                status=200,
                match_querystring=True,
            )

            self.login()
            response = self.client.get(self.url, follow=True)
            self.assertRedirects(response, reverse('new-credits'))


class ProcessedCreditsListViewTestCase(MTPBaseTestCase):

    @property
    def url(self):
        return reverse('processed-credits-list')

    def test_processed_credits_list_view(self):
        with responses.RequestsMock() as rsps:
            self.login()

            rsps.add(
                rsps.GET,
                api_url('/credits/processed/'),
                json={
                    'count': 3,
                    'results': [
                        {
                            'logged_at': '2017-06-04',
                            'owner': 1,
                            'owner_name': 'Clerk 1',
                            'count': 10,
                            'total': 10500,
                            'comment_count': 0
                        },
                        {
                            'logged_at': '2017-06-03',
                            'owner': 1,
                            'owner_name': 'Clerk 1',
                            'count': 4,
                            'total': 6000,
                            'comment_count': 4
                        },
                        {
                            'logged_at': '2017-06-03',
                            'owner': 2,
                            'owner_name': 'Clerk 2',
                            'count': 5,
                            'total': 3200,
                            'comment_count': 5
                        },
                    ]
                },
                status=200,
            )

            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)
            self.assertSequenceEqual(response.context['page_range'], [1])
            self.assertEqual(response.context['current_page'], 1)
            self.assertContains(response, text='10 credits')
            self.assertContains(response, text='4 credits')
            self.assertContains(response, text='5 credits')

    def test_processed_credits_list_view_no_results(self):
        with responses.RequestsMock() as rsps:
            self.login()

            rsps.add(
                rsps.GET,
                api_url('/credits/processed/'),
                json={
                    'count': 0,
                    'results': []
                },
                status=200,
            )

            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, text='No credits')


class ProcessedCreditsDetailViewTestCase(MTPBaseTestCase):

    @property
    def url(self):
        return reverse(
            'processed-credits-detail',
            kwargs={'date': '20170603', 'user_id': 1}
        )

    def test_processed_credits_detail_view(self):
        with responses.RequestsMock() as rsps:
            self.login()

            rsps.add(
                rsps.GET,
                api_url(
                    '/credits/?logged_at__gte=2017-06-03+00:00:00&limit=100'
                    '&logged_at__lt=2017-06-04+00:00:00&user=1'
                    '&log__action=credited&offset=0&ordering=-received_at'
                ),
                json={
                    'count': 2,
                    'results': [
                        {
                            'id': 142,
                            'prisoner_name': 'John Smith',
                            'prisoner_number': 'A1234BC',
                            'amount': 5200,
                            'formatted_amount': '£52.00',
                            'sender_name': 'Fred Smith',
                            'prison': 'BXI',
                            'owner': 1,
                            'owner_name': 'Clerk 1',
                            'received_at': '2017-06-02T12:00:00Z',
                            'resolution': 'credited',
                            'credited_at': '2017-06-03T12:00:00Z',
                            'refunded_at': None,
                        },
                        {
                            'id': 183,
                            'prisoner_name': 'John Smith',
                            'prisoner_number': 'A1234BC',
                            'amount': 2650,
                            'formatted_amount': '£26.50',
                            'sender_name': 'Mary Smith',
                            'prison': 'BXI',
                            'owner': 1,
                            'owner_name': 'Clerk 1',
                            'received_at': '2017-06-01T12:00:00Z',
                            'resolution': 'credited',
                            'credited_at': '2017-06-03T12:00:00Z',
                            'refunded_at': None,
                        },
                    ]
                },
                match_querystring=True,
                status=200,
            )

            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, text='John Smith', count=2)

    def test_processed_credits_detail_view_no_results(self):
        with responses.RequestsMock() as rsps:
            self.login()

            rsps.add(
                rsps.GET,
                api_url(
                    '/credits/?logged_at__gte=2017-06-03+00:00:00&limit=100'
                    '&logged_at__lt=2017-06-04+00:00:00&user=1'
                    '&log__action=credited&offset=0&ordering=-received_at'
                ),
                json={
                    'count': 0,
                    'results': []
                },
                match_querystring=True,
                status=200,
            )

            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, text='No credits')


class SearchViewTestCase(MTPBaseTestCase):

    @property
    def url(self):
        return reverse('search')

    def test_search_view(self):
        with responses.RequestsMock() as rsps:
            self.login()
            login_data = self._default_login_data

            # uncredited
            rsps.add(
                rsps.GET,
                api_url('/credits/'),
                json={
                    'count': 1,
                    'results': [
                        {
                            'id': 200,
                            'prisoner_name': 'HUGH MARSH',
                            'prisoner_number': 'A1235BC',
                            'amount': 1500,
                            'formatted_amount': '£15.00',
                            'sender_name': 'Fred Smith',
                            'prison': 'BXI',
                            'owner': None,
                            'owner_name': None,
                            'received_at': '2017-01-26T12:00:00Z',
                            'resolution': 'pending',
                            'credited_at': None,
                            'refunded_at': None,
                        },
                    ]
                },
                status=200,
            )

            # credited
            rsps.add(
                rsps.GET,
                api_url('/credits/'),
                json={
                    'count': 2,
                    'results': [
                        {
                            'id': 142,
                            'prisoner_name': 'John Smith',
                            'prisoner_number': 'A1234BC',
                            'amount': 5200,
                            'formatted_amount': '£52.00',
                            'sender_name': 'Fred Smith',
                            'prison': 'BXI',
                            'owner': login_data['user_pk'],
                            'owner_name': '%s %s' % (
                                login_data['user_data']['first_name'],
                                login_data['user_data']['last_name'],
                            ),
                            'received_at': '2017-01-25T12:00:00Z',
                            'resolution': 'credited',
                            'credited_at': '2017-01-26T12:00:00Z',
                            'refunded_at': None,
                        },
                        {
                            'id': 183,
                            'prisoner_name': 'John Smith',
                            'prisoner_number': 'A1234BC',
                            'amount': 2650,
                            'formatted_amount': '£26.50',
                            'sender_name': 'Mary Smith',
                            'prison': 'BXI',
                            'owner': login_data['user_pk'],
                            'owner_name': '%s %s' % (
                                login_data['user_data']['first_name'],
                                login_data['user_data']['last_name'],
                            ),
                            'received_at': '2017-01-25T12:00:00Z',
                            'resolution': 'credited',
                            'credited_at': '2017-01-26T12:00:00Z',
                            'refunded_at': None,
                        },
                    ]
                },
                status=200,
            )

            response = self.client.get(self.url, data={
                'search': 'Smith',
            })

        self.assertEqual(response.status_code, 200)
        self.assertSequenceEqual(response.context['page_range'], [1])
        self.assertEqual(response.context['current_page'], 1)
        self.assertEqual(response.context['credit_owner_name'], '%s %s' % (
            login_data['user_data']['first_name'],
            login_data['user_data']['last_name'],
        ))
        self.assertIn('<strong>3</strong> credits', response.content.decode(response.charset))
        self.assertContains(response, text='John Smith', count=2)
