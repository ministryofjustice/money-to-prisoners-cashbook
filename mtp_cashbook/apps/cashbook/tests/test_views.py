import json
from datetime import datetime
import logging

from django.core import mail
from django.core.urlresolvers import reverse
from django.test import override_settings
from mtp_common.test_utils import silence_logger
import responses

from cashbook.tests import MTPBaseTestCase, api_url, nomis_url

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


override_nomis_settings = override_settings(
    NOMIS_API_BASE_URL='https://nomis.local/',
    NOMIS_API_CLIENT_TOKEN='hello',
    NOMIS_API_PRIVATE_KEY=(
        '-----BEGIN EC PRIVATE KEY-----\n'
        'MHcCAQEEIOhhs3RXk8dU/YQE3j2s6u97mNxAM9s+13S+cF9YVgluoAoGCCqGSM49\n'
        'AwEHoUQDQgAE6l49nl7NN6k6lJBfGPf4QMeHNuER/o+fLlt8mCR5P7LXBfMG6Uj6\n'
        'TUeoge9H2N/cCafyhCKdFRdQF9lYB2jB+A==\n'
        '-----END EC PRIVATE KEY-----\n'
    ),  # this key is just for tests, doesn't do anything
)


def wrap_response_data(*args):
    return {
        'count': len(args),
        'results': args
    }


class ChangeNotificationTestCase(MTPBaseTestCase):

    @property
    def url(self):
        return reverse('new-credits')

    @override_nomis_settings
    def test_first_visit_with_nomis_available_shows_change_notification(self):
        self.login()
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, reverse('change-notification'))

    @override_nomis_settings
    def test_second_visit_with_nomis_available_skips_change_notification(self):
        self.login()
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, reverse('change-notification'))

        # second visit
        with responses.RequestsMock() as rsps:
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
                json=wrap_response_data(),
                status=200,
                match_querystring=True,
            )
            response = self.client.get(self.url, follow=True)
            self.assertContains(response, 'New credits')


class NewCreditsViewTestCase(MTPBaseTestCase):
    def setUp(self):
        super().setUp()
        self.set_change_notification_seen()

    @property
    def url(self):
        return reverse('new-credits')

    @override_nomis_settings
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
    @override_nomis_settings
    def test_new_credits_submit(self):
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
                nomis_url('/prison/BXI/offenders/A1234BC/transactions/'),
                json={'id': '6244779-1'},
                status=200,
            )
            rsps.add(
                rsps.POST,
                api_url('/credits/actions/credit/'),
                status=204,
            )
            rsps.add(
                rsps.POST,
                nomis_url('/prison/BXI/offenders/A1234GG/transactions/'),
                json={'id': '6244780-1'},
                status=200,
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
                data={'credits': [1, 2], 'submit_new': None},
                follow=True
            )
            self.assertEqual(response.status_code, 200)
            expected_calls = [
                [{'id': 1, 'credited': True, 'nomis_transaction_id': '6244779-1'}],
                [{'id': 2, 'credited': True, 'nomis_transaction_id': '6244780-1'}]
            ]
            self.assertTrue(
                json.loads(rsps.calls[4].request.body) in expected_calls and
                json.loads(rsps.calls[6].request.body) in expected_calls
            )
            self.assertContains(response, '2 credits sent to NOMIS')
            self.assertEqual(len(mail.outbox), 2)
            self.assertTrue(
                '£52.00' in mail.outbox[0].body and '£45.00' in mail.outbox[1].body or
                '£52.00' in mail.outbox[1].body and '£45.00' in mail.outbox[0].body
            )

    @override_settings(ENVIRONMENT='prod')  # because non-prod environments don't send to .local
    @override_nomis_settings
    def test_new_credits_submit_with_conflict(self):
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
                nomis_url('/prison/BXI/offenders/A1234BC/transactions/'),
                status=409,
            )
            rsps.add(
                rsps.POST,
                api_url('/credits/actions/credit/'),
                status=204,
            )
            rsps.add(
                rsps.POST,
                nomis_url('/prison/BXI/offenders/A1234GG/transactions/'),
                json={'id': '6244780-1'},
                status=200,
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
                    data={'credits': [1, 2], 'submit_new': None},
                    follow=True
                )
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, '2 credits sent to NOMIS')
            self.assertEqual(len(mail.outbox), 2)

    @override_settings(ENVIRONMENT='prod')  # because non-prod environments don't send to .local
    @override_nomis_settings
    def test_new_credits_submit_with_uncreditable(self):
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
                nomis_url('/prison/BXI/offenders/A1234BC/transactions/'),
                status=400,
            )
            rsps.add(
                rsps.POST,
                api_url('/credits/actions/setmanual/'),
                status=204,
            )
            rsps.add(
                rsps.POST,
                nomis_url('/prison/BXI/offenders/A1234GG/transactions/'),
                json={'id': '6244780-1'},
                status=200,
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
            rsps.add(
                rsps.GET,
                nomis_url('/offenders/A1234BC/location/'),
                json={
                    'establishment': {
                        'code': 'LEI',
                        'desc': 'LEEDS (HMP)'
                    }
                },
                status=200,
            )

            self.login()
            with silence_logger(name='mtp', level=logging.CRITICAL):
                response = self.client.post(
                    self.url,
                    data={'credits': [1, 2], 'submit_new': None},
                    follow=True
                )
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, '1 credit sent to NOMIS')
            self.assertContains(response, '1 credit needs your manual input in NOMIS')
            self.assertEqual(len(mail.outbox), 1)

    @override_settings(ENVIRONMENT='prod')  # because non-prod environments don't send to .local
    @override_nomis_settings
    def test_manual_credits_submit(self):
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
                data={'submit_manual_1': None},
                follow=True
            )
            self.assertEqual(
                json.loads(rsps.calls[2].request.body),
                [{'id': 1, 'credited': True}]
            )
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, '1 credit manually input by you into NOMIS')


class ProcessingCreditsViewTestCase(MTPBaseTestCase):
    def setUp(self):
        super().setUp()
        self.set_change_notification_seen()

    @property
    def url(self):
        return reverse('processing-credits')

    @override_nomis_settings
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

    @override_nomis_settings
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

    @override_nomis_settings
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

    @override_nomis_settings
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
    def setUp(self):
        super().setUp()
        self.set_change_notification_seen()

    @property
    def url(self):
        return reverse('processed-credits-list')

    @override_nomis_settings
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

    @override_nomis_settings
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
    def setUp(self):
        super().setUp()
        self.set_change_notification_seen()

    @property
    def url(self):
        return reverse(
            'processed-credits-detail',
            kwargs={'date': '20170603', 'user_id': 1}
        )

    @override_nomis_settings
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

    @override_nomis_settings
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


@override_nomis_settings
class SearchViewTestCase(MTPBaseTestCase):
    def setUp(self):
        super().setUp()
        self.set_change_notification_seen()

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
