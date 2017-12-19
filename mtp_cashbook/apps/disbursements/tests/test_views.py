from django.test import override_settings
from django.urls import reverse
import responses
from mtp_common.test_utils import silence_logger

from cashbook.tests import (
    MTPBaseTestCase, api_url, nomis_url, override_nomis_settings
)
from ..forms import PrisonerForm, AmountForm, SENDING_METHOD
from ..views import DetailsCheckView


class CreateDisbursementFlowTestCase(MTPBaseTestCase):
    prisoner_number = 'A1401AE'
    nomis_id = 'BXI'

    def enter_prisoner_details(self):
        responses.add(
            responses.GET,
            api_url('/prisoner_locations/{prisoner_number}/'.format(
                prisoner_number=self.prisoner_number
            )),
            json={
                'prisoner_number': self.prisoner_number,
                'prisoner_dob': '1970-01-01',
                'prisoner_name': 'JILLY HALL',
                'prison': self.nomis_id
            },
            status=200,
        )

        return self.client.post(
            reverse('disbursements:prisoner'),
            data={'prisoner_number': self.prisoner_number},
            follow=True
        )

    def enter_amount(self, amount=10, cash=5000):
        responses.add(
            responses.GET,
            nomis_url('/prison/{nomis_id}/offenders/{prisoner_number}/accounts/'.format(
                nomis_id=self.nomis_id, prisoner_number=self.prisoner_number
            )),
            json={
                'cash': cash,
                'spends': 2000,
                'savings': 10000
            },
            status=200,
        )

        return self.client.post(
            reverse('disbursements:amount'),
            data={'amount': amount},
            follow=True
        )

    def choose_sending_method(self, method=SENDING_METHOD.BANK_TRANSFER):
        return self.client.post(
            reverse('disbursements:sending_method'),
            data={
                'sending_method': method
            },
            follow=True
        )

    def enter_recipient_details(self, data=None):
        data = data or {
            'recipient_first_name': 'John',
            'recipient_last_name': 'Smith',
            'address_line1': '54 Fake Road',
            'address_line2': '',
            'city': 'London',
            'postcode': 'n17 9bj',
            'email': 'recipient@mtp.local',
        }
        return self.client.post(
            reverse('disbursements:recipient_contact'),
            data=data, follow=True,
        )

    def enter_recipient_bank_account(self, data=None):
        data = data or {
            'sort_code': '60-57-89',
            'account_number': '90908787',
        }
        return self.client.post(
            reverse('disbursements:recipient_bank_account'),
            data=data, follow=True,
        )


class PrisonerTestCase(CreateDisbursementFlowTestCase):

    @property
    def url(self):
        return reverse('disbursements:prisoner')

    @responses.activate
    @override_settings(DISBURSEMENT_PRISONS=['BXI'])
    def test_valid_prisoner_number(self):
        self.login()
        self.choose_sending_method(method=SENDING_METHOD.BANK_TRANSFER)
        response = self.enter_prisoner_details()
        self.assertOnPage(response, 'prisoner_check')

    @responses.activate
    @override_settings(DISBURSEMENT_PRISONS=['BXI'])
    def test_invalid_prisoner_number(self):
        prisoner_number = 'A1404AE'
        responses.add(
            responses.GET,
            api_url('/prisoner_locations/{prisoner_number}/'.format(
                prisoner_number=prisoner_number
            )),
            status=404,
        )

        self.login()
        self.choose_sending_method(method=SENDING_METHOD.BANK_TRANSFER)
        response = self.client.post(
            self.url,
            data={'prisoner_number': prisoner_number},
            follow=True
        )

        self.assertOnPage(response, 'prisoner')
        self.assertContains(response, PrisonerForm.error_messages['not_found'])

    @responses.activate
    @override_settings(DISBURSEMENT_PRISONS=['BXI'])
    def test_prisoner_in_different_prison(self):
        prisoner_number = 'A1404AE'
        responses.add(
            responses.GET,
            api_url('/prisoner_locations/{prisoner_number}/'.format(
                prisoner_number=prisoner_number
            )),
            status=403,
        )

        self.login()
        self.choose_sending_method(method=SENDING_METHOD.BANK_TRANSFER)
        response = self.client.post(
            self.url,
            data={'prisoner_number': prisoner_number},
            follow=True
        )

        self.assertOnPage(response, 'prisoner')
        self.assertContains(response, PrisonerForm.error_messages['wrong_prison'])


class AmountTestCase(CreateDisbursementFlowTestCase):

    @property
    def url(self):
        return reverse('disbursements:amount')

    @responses.activate
    @override_nomis_settings
    @override_settings(DISBURSEMENT_PRISONS=['BXI'])
    def test_valid_amount(self):
        self.login()
        self.choose_sending_method(method=SENDING_METHOD.CHEQUE)
        self.enter_prisoner_details()
        response = self.enter_amount(amount=10, cash=5000)

        self.assertOnPage(response, 'recipient_contact')

    @responses.activate
    @override_nomis_settings
    @override_settings(DISBURSEMENT_PRISONS=['BXI'])
    def test_too_high_amount(self):
        self.login()
        self.choose_sending_method(method=SENDING_METHOD.BANK_TRANSFER)
        self.enter_prisoner_details()
        response = self.enter_amount(amount=60, cash=5000)

        self.assertOnPage(response, 'amount')
        self.assertContains(response, AmountForm.error_messages['exceeds_funds'])

    @responses.activate
    @override_nomis_settings
    @override_settings(DISBURSEMENT_PRISONS=['BXI'])
    def test_nomis_unavailable(self):
        self.login()
        self.choose_sending_method(method=SENDING_METHOD.BANK_TRANSFER)
        self.enter_prisoner_details()
        response = self.client.get(self.url)

        self.assertOnPage(response, 'amount')
        self.assertContains(response, 'Unknown')


class SendingMethodTestCase(CreateDisbursementFlowTestCase):

    @responses.activate
    @override_nomis_settings
    @override_settings(DISBURSEMENT_PRISONS=['BXI'])
    def test_cheque_sending_method_skips_bank_account(self):
        self.login()
        self.choose_sending_method(method=SENDING_METHOD.CHEQUE)
        self.enter_prisoner_details()
        self.enter_amount()

        response = self.enter_recipient_details()

        self.assertOnPage(response, 'details_check')
        content = response.content.decode(response.charset)
        self.assertIn('John', content)
        self.assertIn('Smith', content)
        self.assertIn('Fake', content)
        self.assertIn('London', content)
        self.assertIn('N17 9BJ', content)
        self.assertIn('JILLY', content)

    @responses.activate
    @override_nomis_settings
    @override_settings(DISBURSEMENT_PRISONS=['BXI'])
    def test_cheque_sending_method_includes_bank_account(self):
        self.login()
        self.choose_sending_method(method=SENDING_METHOD.BANK_TRANSFER)
        self.enter_prisoner_details()
        self.enter_amount()

        response = self.enter_recipient_details()

        self.assertOnPage(response, 'recipient_bank_account')


class RecipientContactTestCase(CreateDisbursementFlowTestCase):
    @property
    def url(self):
        return reverse('disbursements:recipient_contact')

    @responses.activate
    @override_nomis_settings
    @override_settings(DISBURSEMENT_PRISONS=['BXI'])
    def test_contact_details_required(self):
        self.login()
        self.choose_sending_method(method=SENDING_METHOD.BANK_TRANSFER)
        self.enter_prisoner_details()
        self.enter_amount()

        response = self.enter_recipient_details({
            'recipient_first_name': 'John',
            'recipient_last_name': 'Smith',
            'city': 'London',
            'postcode': 'n17 9bj',
        })
        self.assertOnPage(response, 'recipient_contact')
        self.assertFormError(response, 'form', 'address_line1', 'This field is required')


class RecipientBankAccountTestCase(CreateDisbursementFlowTestCase):
    @property
    def url(self):
        return reverse('disbursements:recipient_bank_account')

    @responses.activate
    @override_nomis_settings
    @override_settings(DISBURSEMENT_PRISONS=['BXI'])
    def test_account_details_required(self):
        self.login()
        self.choose_sending_method(method=SENDING_METHOD.BANK_TRANSFER)
        self.enter_prisoner_details()
        self.enter_amount()
        self.enter_recipient_details()
        response = self.enter_recipient_bank_account({'sort_code': ''})
        self.assertOnPage(response, 'recipient_bank_account')
        self.assertFormError(response, 'form', 'sort_code', 'This field is required')
        self.assertFormError(response, 'form', 'account_number', 'This field is required')

    @responses.activate
    @override_nomis_settings
    @override_settings(DISBURSEMENT_PRISONS=['BXI'])
    def test_account_details_validity(self):
        self.login()
        self.choose_sending_method(method=SENDING_METHOD.BANK_TRANSFER)
        self.enter_prisoner_details()
        self.enter_amount()
        self.enter_recipient_details()
        response = self.enter_recipient_bank_account({
            'sort_code': '60-57-89a',
            'account_number': '9090878',
        })
        self.assertOnPage(response, 'recipient_bank_account')
        self.assertFormError(response, 'form', 'sort_code', 'The sort code should be 6 digits long')
        self.assertFormError(response, 'form', 'account_number', 'The account number should be 8 digits long')


class DisbursementCompleteTestCase(CreateDisbursementFlowTestCase):

    @property
    def url(self):
        return reverse('disbursements:prisoner')

    @responses.activate
    @override_nomis_settings
    @override_settings(DISBURSEMENT_PRISONS=['BXI'])
    def test_create_valid_bank_transfer_disbursement(self):
        responses.add(
            responses.POST,
            api_url('/disbursements/'),
            json={'id': 1},
            status=200,
        )

        self.login()
        self.choose_sending_method(method=SENDING_METHOD.BANK_TRANSFER)
        self.enter_prisoner_details()
        self.enter_amount()
        self.enter_recipient_details()
        self.enter_recipient_bank_account()
        response = self.client.get(reverse('disbursements:complete'), follow=True)

        self.assertOnPage(response, 'complete')

    @responses.activate
    @override_nomis_settings
    @override_settings(DISBURSEMENT_PRISONS=['BXI'])
    def test_create_valid_cheque_disbursement(self):
        responses.add(
            responses.POST,
            api_url('/disbursements/'),
            json={'id': 1},
            status=200,
        )

        self.login()
        self.choose_sending_method(method=SENDING_METHOD.CHEQUE)
        self.enter_prisoner_details()
        self.enter_amount()
        self.enter_recipient_details()
        response = self.client.get(reverse('disbursements:complete'), follow=True)

        self.assertOnPage(response, 'complete')

    @responses.activate
    @override_nomis_settings
    @override_settings(DISBURSEMENT_PRISONS=['BXI'])
    def test_create_disbursement_service_unavailable(self):
        self.login()
        self.choose_sending_method(method=SENDING_METHOD.BANK_TRANSFER)
        self.enter_prisoner_details()
        self.enter_amount()
        self.enter_recipient_details()
        self.enter_recipient_bank_account()
        with silence_logger():
            response = self.client.get(reverse('disbursements:complete'), follow=True)

        self.assertOnPage(response, 'details_check')
        self.assertContains(response, DetailsCheckView.error_messages['connection'])
