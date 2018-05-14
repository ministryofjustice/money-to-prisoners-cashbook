from django.test import override_settings
from django.urls import reverse
import responses
from mtp_common.test_utils import silence_logger

from cashbook.tests import (
    MTPBaseTestCase, api_url, nomis_url, override_nomis_settings
)
from ..forms import PrisonerForm, AmountForm, SENDING_METHOD
from ..views import HandoverView


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
                'method': method
            },
            follow=True
        )

    def enter_recipient_details(self, data=None):
        data = data or {
            'recipient_type': 'person',
            'recipient_first_name': 'John',
            'recipient_last_name': 'Smith',
            'address_line1': '54 Fake Road',
            'address_line2': '',
            'city': 'London',
            'postcode': 'n17 9bj',
            'recipient_email': 'recipient@mtp.local',
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

    def enter_remittance_description(self, remittance_description=''):
        data = {
            'remittance': 'yes' if remittance_description else 'no',
            'remittance_description': remittance_description,
        }
        return self.client.post(
            reverse('disbursements:remittance_description'),
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
        self.assertOnPage(response, 'disbursements:prisoner_check')

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

        self.assertOnPage(response, 'disbursements:prisoner')
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

        self.assertOnPage(response, 'disbursements:prisoner')
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

        self.assertOnPage(response, 'disbursements:recipient_contact')

    @responses.activate
    @override_nomis_settings
    @override_settings(DISBURSEMENT_PRISONS=['BXI'])
    def test_too_high_amount(self):
        self.login()
        self.choose_sending_method(method=SENDING_METHOD.BANK_TRANSFER)
        self.enter_prisoner_details()
        response = self.enter_amount(amount=60, cash=5000)

        self.assertOnPage(response, 'disbursements:amount')
        self.assertContains(response, AmountForm.error_messages['exceeds_funds'])

    @responses.activate
    @override_nomis_settings
    @override_settings(DISBURSEMENT_PRISONS=['BXI'])
    def test_nomis_unavailable(self):
        self.login()
        self.choose_sending_method(method=SENDING_METHOD.BANK_TRANSFER)
        self.enter_prisoner_details()
        response = self.client.get(self.url)

        self.assertOnPage(response, 'disbursements:amount')
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

        self.enter_recipient_details()
        response = self.enter_remittance_description()

        self.assertOnPage(response, 'disbursements:details_check')
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

        self.assertOnPage(response, 'disbursements:recipient_bank_account')


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
            'recipient_type': 'person',
            'recipient_first_name': 'John',
            'recipient_last_name': 'Smith',
            'city': 'London',
            'postcode': 'n17 9bj',
        })
        self.assertOnPage(response, 'disbursements:recipient_contact')
        self.assertFormError(response, 'form', 'address_line1', 'This field is required')

    @responses.activate
    @override_nomis_settings
    @override_settings(DISBURSEMENT_PRISONS=['BXI'])
    def test_first_name_required(self):
        self.login()
        self.choose_sending_method(method=SENDING_METHOD.BANK_TRANSFER)
        self.enter_prisoner_details()
        self.enter_amount()

        response = self.enter_recipient_details({
            'recipient_type': 'person',
            'recipient_first_name': '',
            'recipient_last_name': 'Smith',
            'address_line1': '10 Fake Road',
            'city': 'London',
            'postcode': 'n17 9bj',
        })
        self.assertOnPage(response, 'disbursements:recipient_contact')
        self.assertFormError(response, 'form', 'recipient_first_name', 'This field is required')

    @responses.activate
    @override_nomis_settings
    @override_settings(DISBURSEMENT_PRISONS=['BXI'])
    def test_last_name_required(self):
        self.login()
        self.choose_sending_method(method=SENDING_METHOD.BANK_TRANSFER)
        self.enter_prisoner_details()
        self.enter_amount()

        response = self.enter_recipient_details({
            'recipient_type': 'person',
            'recipient_first_name': 'John',
            'recipient_last_name': '',
            'address_line1': '10 Fake Road',
            'city': 'London',
            'postcode': 'n17 9bj',
        })
        self.assertOnPage(response, 'disbursements:recipient_contact')
        self.assertFormError(response, 'form', 'recipient_last_name', 'This field is required')

    @responses.activate
    @override_nomis_settings
    @override_settings(DISBURSEMENT_PRISONS=['BXI'])
    def test_company_name_required(self):
        self.login()
        self.choose_sending_method(method=SENDING_METHOD.BANK_TRANSFER)
        self.enter_prisoner_details()
        self.enter_amount()

        response = self.enter_recipient_details({
            'recipient_type': 'company',
            'recipient_company_name': '',
            'address_line1': '10 Fake Road',
            'city': 'London',
            'postcode': 'n17 9bj',
        })
        self.assertOnPage(response, 'disbursements:recipient_contact')
        self.assertFormError(response, 'form', 'recipient_company_name', 'This field is required')


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
        self.assertOnPage(response, 'disbursements:recipient_bank_account')
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
        self.assertOnPage(response, 'disbursements:recipient_bank_account')
        self.assertFormError(response, 'form', 'sort_code', 'The sort code should be 6 digits long')
        self.assertFormError(response, 'form', 'account_number', 'The account number should be 8 digits long')

    @responses.activate
    @override_nomis_settings
    @override_settings(DISBURSEMENT_PRISONS=['BXI'])
    def test_building_society_account_detected(self):
        self.login()
        self.choose_sending_method(method=SENDING_METHOD.BANK_TRANSFER)
        self.enter_prisoner_details()
        self.enter_amount()
        self.enter_recipient_details()
        response = self.enter_recipient_bank_account({
            'sort_code': '40-32-14',
            'account_number': '10572780',
        })
        self.assertOnPage(response, 'disbursements:recipient_bank_account')
        self.assertFormError(
            response, 'form', 'roll_number',
            'This is a building society account. ' +
            'Contact the prisoner to get the building society roll number or send a cheque.'
        )

    @responses.activate
    @override_nomis_settings
    @override_settings(DISBURSEMENT_PRISONS=['BXI'])
    def test_non_building_society_account_detected(self):
        self.login()
        self.choose_sending_method(method=SENDING_METHOD.BANK_TRANSFER)
        self.enter_prisoner_details()
        self.enter_amount()
        self.enter_recipient_details()
        response = self.enter_recipient_bank_account({
            'sort_code': '60-70-80',
            'account_number': '10572780',
            'roll_number': '12345678',
        })
        self.assertOnPage(response, 'disbursements:recipient_bank_account')
        self.assertFormError(
            response, 'form', 'roll_number',
            'You don’t need a roll number because this is not a building society account.'
        )

    @responses.activate
    @override_nomis_settings
    @override_settings(DISBURSEMENT_PRISONS=['BXI'])
    def test_building_society_roll_number_validation_failure(self):
        self.login()
        self.choose_sending_method(method=SENDING_METHOD.BANK_TRANSFER)
        self.enter_prisoner_details()
        self.enter_amount()
        self.enter_recipient_details()
        response = self.enter_recipient_bank_account({
            'sort_code': '40-32-14',
            'account_number': '10572780',
            'roll_number': '12345678',
        })
        self.assertOnPage(response, 'disbursements:recipient_bank_account')
        self.assertFormError(
            response, 'form', 'roll_number',
            'This roll number is not valid for this type of account. ' +
            'Contact the prisoner to get the correct building society roll number or send a cheque.'
        )

    @responses.activate
    @override_nomis_settings
    @override_settings(DISBURSEMENT_PRISONS=['BXI'])
    def test_building_society_roll_number_validation_success(self):
        self.login()
        self.choose_sending_method(method=SENDING_METHOD.BANK_TRANSFER)
        self.enter_prisoner_details()
        self.enter_amount()
        self.enter_recipient_details()
        response = self.enter_recipient_bank_account({
            'sort_code': '40-32-14',
            'account_number': '10572780',
            'roll_number': 'ABC1234567DEF',
        })
        self.assertOnPage(response, 'disbursements:remittance_description')


class RemittanceDescriptionTestCase(CreateDisbursementFlowTestCase):
    @property
    def url(self):
        return reverse('disbursements:remittance_description')

    @responses.activate
    @override_nomis_settings
    @override_settings(DISBURSEMENT_PRISONS=['BXI'])
    def test_remittance_choice_required(self):
        self.login()
        self.choose_sending_method(method=SENDING_METHOD.CHEQUE)
        self.enter_prisoner_details()
        self.enter_amount()
        response = self.enter_recipient_details()
        self.assertOnPage(response, 'disbursements:remittance_description')
        response = self.client.post(self.url, data={'remittance_description': 'payment for housing'})
        self.assertOnPage(response, 'disbursements:remittance_description')
        self.assertContains(response, 'Please select ‘yes’ or ‘no’')

    @responses.activate
    @override_nomis_settings
    @override_settings(DISBURSEMENT_PRISONS=['BXI'])
    def test_remittance_being_empty(self):
        self.login()
        self.choose_sending_method(method=SENDING_METHOD.CHEQUE)
        self.enter_prisoner_details()
        self.enter_amount()
        self.enter_recipient_details()
        response = self.enter_remittance_description('')
        self.assertOnPage(response, 'disbursements:details_check')
        self.assertContains(response, 'None given')

    @responses.activate
    @override_nomis_settings
    @override_settings(DISBURSEMENT_PRISONS=['BXI'])
    def test_remittance_description(self):
        self.login()
        self.choose_sending_method(method=SENDING_METHOD.CHEQUE)
        self.enter_prisoner_details()
        self.enter_amount()
        self.enter_recipient_details()
        response = self.enter_remittance_description('payment for housing')
        self.assertOnPage(response, 'disbursements:details_check')
        self.assertContains(response, 'payment for housing')
        self.assertNotContains(response, 'None given')


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
        self.enter_amount(10)
        self.enter_recipient_details()
        self.enter_recipient_bank_account()
        self.enter_remittance_description()

        response = self.client.post(reverse('disbursements:created'), follow=True)
        self.assertOnPage(response, 'disbursements:created')

        post_requests = [call.request for call in responses.calls if call.request.method == responses.POST]
        self.assertEqual(len(post_requests), 1)
        self.assertJSONEqual(post_requests[0].body.decode(), {
            'method': SENDING_METHOD.BANK_TRANSFER,
            'prisoner_number': self.prisoner_number,
            'prison': 'BXI',
            'prisoner_name': 'JILLY HALL',
            'amount': 1000,
            'sort_code': '605789',
            'account_number': '90908787',
            'roll_number': '',
            'recipient_is_company': False,
            'recipient_first_name': 'John',
            'recipient_last_name': 'Smith',
            'address_line1': '54 Fake Road',
            'address_line2': '',
            'city': 'London',
            'postcode': 'N17 9BJ',
            'recipient_email': 'recipient@mtp.local',
            'remittance_description': '',
        })

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
        self.enter_remittance_description()
        response = self.client.post(reverse('disbursements:created'), follow=True)

        self.assertOnPage(response, 'disbursements:created')

    @responses.activate
    @override_nomis_settings
    @override_settings(DISBURSEMENT_PRISONS=['BXI'])
    def test_create_edited_valid_company_cheque_disbursement(self):
        responses.add(
            responses.POST,
            api_url('/disbursements/'),
            json={'id': 1},
            status=200,
        )

        self.login()
        self.choose_sending_method(method=SENDING_METHOD.CHEQUE)
        self.enter_prisoner_details()
        self.enter_amount(10)
        self.enter_recipient_details()
        self.enter_remittance_description()
        response = self.client.get(reverse('disbursements:details_check'))
        self.assertContains(response, 'John')
        self.assertContains(response, 'Smith')

        # edit recipient
        self.enter_recipient_details({
            'recipient_type': 'company',
            'recipient_company_name': 'Boots',
            'recipient_first_name': '',
            'recipient_last_name': '',
            'address_line1': '54 Fake Road',
            'address_line2': '',
            'city': 'London',
            'postcode': 'n17 9bj',
            'recipient_email': 'recipient@mtp.local',
        })
        response = self.client.get(reverse('disbursements:details_check'))
        self.assertContains(response, 'Boots')
        self.assertNotContains(response, 'John')
        self.assertNotContains(response, 'Smith')

        # save
        response = self.client.post(reverse('disbursements:created'), follow=True)
        self.assertOnPage(response, 'disbursements:created')

        post_requests = [call.request for call in responses.calls if call.request.method == responses.POST]
        self.assertEqual(len(post_requests), 1)
        self.assertJSONEqual(post_requests[0].body.decode(), {
            'method': SENDING_METHOD.CHEQUE,
            'prisoner_number': self.prisoner_number,
            'prison': 'BXI',
            'prisoner_name': 'JILLY HALL',
            'amount': 1000,
            'recipient_is_company': True,
            'recipient_first_name': '',
            'recipient_last_name': 'Boots',
            'address_line1': '54 Fake Road',
            'address_line2': '',
            'city': 'London',
            'postcode': 'N17 9BJ',
            'recipient_email': 'recipient@mtp.local',
            'remittance_description': '',
        })

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
        self.enter_remittance_description()
        with silence_logger():
            response = self.client.post(reverse('disbursements:created'), follow=True)

        self.assertOnPage(response, 'disbursements:handover')
        self.assertContains(response, HandoverView.error_messages['connection'])
