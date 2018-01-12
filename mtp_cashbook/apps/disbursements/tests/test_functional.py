from django.test import override_settings
from django.utils.crypto import get_random_string
from selenium.common.exceptions import InvalidElementStateException

from cashbook.tests.test_functional import CashbookTestCase
from disbursements.templatetags.disbursements import format_sortcode


@override_settings(DISBURSEMENT_PRISONS=['LEI'])
class DisbursementTestCase(CashbookTestCase):
    def test_create_bank_transfer_disbursement(self):
        self.login(self.username, self.username)

        self.assertShowingView('home')
        self.click_on_text('Digital disbursements')

        self.assertShowingView('disbursements:start')
        self.click_on_link('Start now')

        self.assertShowingView('disbursements:sending_method')
        self.click_on_text_substring('Bank transfer')
        self.click_on_text_substring('Next')

        self.assertShowingView('disbursements:prisoner')
        self.fill_in_form({
            'id_prisoner_number': 'A1401AE',
        })
        self.click_on_text_substring('Next')

        self.assertShowingView('disbursements:prisoner_check')
        self.assertInSource('JILLY HALL')
        self.click_on_text_substring('Yes')
        self.click_on_text_substring('Next')

        self.assertShowingView('disbursements:amount')
        self.fill_in_form({
            'id_amount': '11a',
        })
        self.click_on_text_substring('Confirm')
        self.assertShowingView('disbursements:amount')
        self.assertInSource('Enter a number')
        self.get_element('id_amount').clear()
        self.fill_in_form({
            'id_amount': '11',
        })
        self.click_on_text_substring('Confirm')

        self.assertShowingView('disbursements:recipient_contact')
        contact_form = {
            'id_recipient_first_name': 'Mary-' + get_random_string(3),
            'id_recipient_last_name': 'Halls-' + get_random_string(3),
            'id_address_line1': 'Street-' + get_random_string(3),
            'id_city': 'City-' + get_random_string(3),
            'id_postcode': 'PostCode-' + get_random_string(3),
            'id_email': 'mary-halls-' + get_random_string(3) + '@outside.local',
        }
        self.fill_in_form(contact_form)
        self.click_on_text_substring('Next')

        self.assertShowingView('disbursements:recipient_bank_account')
        self.assertInSource('%s %s' % (contact_form['id_recipient_first_name'],
                                       contact_form['id_recipient_last_name']))
        bank_account = {
            'id_sort_code': get_random_string(6, '0123456789'),
            'id_account_number': get_random_string(8, '0123456789'),
        }
        self.fill_in_form(bank_account)
        self.click_on_text_substring('Next')

        self.assertShowingView('disbursements:details_check')
        self.assertInSource('Bank transfer')
        self.assertInSource('£11.00')
        for key in ('id_recipient_first_name', 'id_recipient_last_name', 'id_address_line1', 'id_city', 'id_email'):
            self.assertInSource(contact_form[key])
        self.assertInSource(contact_form['id_postcode'].upper())
        self.assertInSource(format_sortcode(bank_account['id_sort_code']))
        self.assertInSource(bank_account['id_account_number'])
        self.assertInSource('JILLY HALL')
        self.assertInSource('A1401AE')
        self.click_on_text_substring('No')
        try:
            self.click_on_text_substring('Next')
        except InvalidElementStateException:
            pass
        self.assertShowingView('disbursements:details_check')
        self.click_on_text_substring('Yes')
        self.click_on_text_substring('Next')

        self.assertShowingView('disbursements:hand-over')
        self.get_element('.button').click()

        self.assertShowingView('disbursements:complete')
        self.assertInSource('request is ready for your colleague')

        # search for new request
        self.click_on_link('Payments made')

        self.assertShowingView('disbursements:search')
        self.click_on_link('Recipient')
        self.type_in('id_recipient_name', contact_form['id_recipient_first_name'], send_return=True)
        self.assertShowingView('disbursements:search')
        self.assertNotInSource('There was a problem')
        self.get_element('id_recipient_name').clear()

        self.assertInSource('Entered by HMP LEEDS Clerk')
        self.assertInSource('Waiting for confirmation')
        self.assertInSource('Bank transfer')
        self.assertInSource('£11.00')
        for key in ('id_recipient_first_name', 'id_recipient_last_name', 'id_address_line1', 'id_city'):
            self.assertInSource(contact_form[key])
        self.assertInSource(contact_form['id_postcode'].upper())
        self.assertInSource(format_sortcode(bank_account['id_sort_code']))
        self.assertInSource(bank_account['id_account_number'])
        self.assertInSource('JILLY HALL')
        self.assertInSource('A1401AE')

    def test_create_cheque_disbursement(self):
        self.login(self.username, self.username)

        self.assertShowingView('home')
        self.click_on_text('Digital disbursements')

        self.assertShowingView('disbursements:start')
        self.click_on_link('Start now')

        self.assertShowingView('disbursements:sending_method')
        self.click_on_text_substring('Cheque')
        self.click_on_text_substring('Next')

        self.assertShowingView('disbursements:prisoner')
        self.fill_in_form({
            'id_prisoner_number': 'A1401AE',
        })
        self.click_on_text_substring('Next')

        self.assertShowingView('disbursements:prisoner_check')
        self.assertInSource('JILLY HALL')
        self.click_on_text_substring('Yes')
        self.click_on_text_substring('Next')

        self.assertShowingView('disbursements:amount')
        self.fill_in_form({
            'id_amount': '11a',
        })
        self.click_on_text_substring('Confirm')
        self.assertShowingView('disbursements:amount')
        self.assertInSource('Enter a number')
        self.get_element('id_amount').clear()
        self.fill_in_form({
            'id_amount': '11',
        })
        self.click_on_text_substring('Confirm')

        self.assertShowingView('disbursements:recipient_contact')
        contact_form = {
            'id_recipient_first_name': 'Mary-' + get_random_string(3),
            'id_recipient_last_name': 'Halls-' + get_random_string(3),
            'id_address_line1': 'Street-' + get_random_string(3),
            'id_city': 'City-' + get_random_string(3),
            'id_postcode': 'PostCode-' + get_random_string(3),
            'id_email': 'mary-halls-' + get_random_string(3) + '@outside.local',
        }
        self.fill_in_form(contact_form)
        self.click_on_text_substring('Next')

        self.assertShowingView('disbursements:details_check')
        self.assertInSource('Cheque')
        self.assertInSource('£11.00')
        for key in ('id_recipient_first_name', 'id_recipient_last_name', 'id_address_line1', 'id_city', 'id_email'):
            self.assertInSource(contact_form[key])
        self.assertInSource(contact_form['id_postcode'].upper())
        self.assertInSource('JILLY HALL')
        self.assertInSource('A1401AE')
        self.click_on_text_substring('No')
        try:
            self.click_on_text_substring('Next')
        except InvalidElementStateException:
            pass
        self.assertShowingView('disbursements:details_check')
        self.click_on_text_substring('Yes')
        self.click_on_text_substring('Next')

        self.assertShowingView('disbursements:hand-over')
        self.get_element('.button').click()

        self.assertShowingView('disbursements:complete')
        self.assertInSource('request is ready for your colleague')

        # search for new request
        self.click_on_link('Payments made')

        self.assertShowingView('disbursements:search')
        self.click_on_link('Recipient')
        self.type_in('id_recipient_name', contact_form['id_recipient_first_name'], send_return=True)
        self.assertShowingView('disbursements:search')
        self.assertNotInSource('There was a problem')
        self.get_element('id_recipient_name').clear()

        self.assertInSource('Entered by HMP LEEDS Clerk')
        self.assertInSource('Waiting for confirmation')
        self.assertInSource('Cheque')
        self.assertInSource('£11.00')
        for key in ('id_recipient_first_name', 'id_recipient_last_name', 'id_address_line1', 'id_city'):
            self.assertInSource(contact_form[key])
        self.assertInSource(contact_form['id_postcode'].upper())
        self.assertInSource('JILLY HALL')
        self.assertInSource('A1401AE')
