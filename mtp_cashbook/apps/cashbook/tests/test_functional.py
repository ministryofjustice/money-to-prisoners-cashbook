import logging
import re

from mtp_utils.test_utils.functional_tests import FunctionalTestCase

logger = logging.getLogger('mtp')


class CashbookTestCase(FunctionalTestCase):
    """
    Base class to define common methods to test subclasses below
    """
    auto_load_test_data = True
    accessibility_scope_selector = '#content'

    def login_and_go_to(self, link_text):
        self.login('test-prison-1', 'test-prison-1')
        self.click_on_text(link_text)

    def click_select_all_payments(self):
        self.get_element('//label[@for="select-all-header"]').click()

    def click_done_payment(self, row):
        xpath = '//input[@type="checkbox" and @data-amount][%d]' % row
        checkbox_id = self.get_element(xpath).get_attribute('id')
        self.get_element('//label[@for="%s"]' % checkbox_id).click()


class LoginTests(CashbookTestCase):
    """
    Tests for Login page
    """

    def test_title(self):
        self.driver.get(self.live_server_url)
        heading = self.driver.find_element_by_tag_name('h1')
        self.assertEqual('Money sent to prisoners', heading.text)
        self.assertCssProperty('h1', 'font-size', '48px')

    def test_bad_login(self):
        self.login('test-prison-1', 'bad-password')
        self.assertInSource('There was a problem submitting the form')

    def test_good_login(self):
        self.login('test-prison-1', 'test-prison-1')
        self.assertCurrentUrl('/')
        self.assertInSource('Credits to process')

    def test_logout(self):
        self.login('test-prison-1', 'test-prison-1')
        self.click_on_text('Sign out')
        self.assertCurrentUrl('/login/')


class LockedPaymentsPageTests(CashbookTestCase):
    """
    Tests for Locked Payments page
    """

    def setUp(self):
        super().setUp()
        self.login_and_go_to('In progress')

    def test_going_to_the_locked_payments_page(self):
        self.assertInSource('Credits in progress')
        self.assertInSource('Staff name')
        self.assertInSource('Time in progress')

    def test_help_popup(self):
        help_box_heading = self.driver.find_element_by_css_selector('.help-box-title')
        self.assertCssProperty('.help-box-contents', 'display', 'none')
        self.assertEqual('false', help_box_heading.get_attribute('aria-expanded'))
        self.click_on_text('Help')
        self.assertCssProperty('.help-box-contents', 'display', 'block')
        self.assertEqual('true', help_box_heading.get_attribute('aria-expanded'))
        self.click_on_text('Help')
        self.assertCssProperty('.help-box-contents', 'display', 'none')
        self.assertEqual('false', help_box_heading.get_attribute('aria-expanded'))


class NewPaymentsPageTests(CashbookTestCase):
    """
    Tests for New Payments page
    """

    def setUp(self):
        super().setUp()
        self.login_and_go_to('New')

    def test_going_to_the_credits_page(self):
        self.assertInSource('New credits')
        self.assertInSource('Control total')

    def test_submitting_payments_credited(self):
        self.click_done_payment(row=1)
        self.click_on_text('Done')
        self.assertIsNotNone(self.driver.find_element_by_xpath(
            '//div[@class="Dialog-inner"]/h3[text()="Are you sure?"]'
        ))

    def test_submitting_and_confirming_partial_batch(self):
        self.click_done_payment(row=1)
        self.click_on_text('Done')
        self.click_on_text('Yes')
        self.assertInSource('You’ve credited 1 payment to NOMIS.')
        self.assertEqual('Digital cashbook', self.driver.title)

    def test_submitting_and_not_confirming_partial_batch(self):
        self.click_done_payment(row=1)
        self.click_on_text('Done')
        self.click_on_text('No, continue processing')
        self.assertEqual('New credits - Digital cashbook', self.driver.title)

    def test_clicking_done_with_no_payments_credited(self):
        self.click_on_text('Done')
        self.assertIsNotNone(self.driver.find_element_by_xpath(
            '//div[@class="error-summary"]/h1[text()="You have not ticked any credits"]'
        ))

    def test_printing(self):
        self.click_on_text('Print these payments')
        self.assertIsNotNone(self.driver.find_element_by_xpath(
            '//div[@class="Dialog-inner"]/h3[text()="Do you need to print?"]'
        ))

    def test_help_popup(self):
        help_box_heading = self.driver.find_element_by_css_selector('.help-box-title')
        self.assertCssProperty('.help-box-contents', 'display', 'none')
        self.assertEqual('false', help_box_heading.get_attribute('aria-expanded'))
        self.click_on_text('Help')
        self.assertCssProperty('.help-box-contents', 'display', 'block')
        self.assertEqual('true', help_box_heading.get_attribute('aria-expanded'))
        self.click_on_text('Help')
        self.assertCssProperty('.help-box-contents', 'display', 'none')
        self.assertEqual('false', help_box_heading.get_attribute('aria-expanded'))

    def test_go_back_home(self):
        self.click_on_text('Home')
        self.assertEqual('Digital cashbook', self.driver.title)
        self.assertCurrentUrl('/dashboard-batch-discard/')

    def test_submitting_complete_batch(self):
        self.click_select_all_payments()
        self.click_on_text('Done')
        self.assertEqual('Digital cashbook', self.driver.title)
        self.assertInSource('You’ve credited')

    def test_checkboxes_style(self):
        # Regression tests for https://www.pivotaltracker.com/story/show/115328657
        self.click_on_text('Print these payments')
        self.assertCssProperty('label[for=remove-print-prompt]', 'background-position', '0% 0%')
        # remember_checkbox = self.driver.find_element_by_xpath('//label[@for="remove-print-prompt"]')
        # self.assertEqual('0% 0%', remember_checkbox.value_of_css_property('background-position'))
        self.click_on_text('close')
        self.assertCssProperty('label[for=select-all-header]', 'background-position', '0% 0%')

        # select_all_checkbox = self.driver.find_element_by_xpath('//label[@for="select-all-header"][1]')
        # self.assertEqual('0% 0%', select_all_checkbox.value_of_css_property('background-position'))


class VisualTests(CashbookTestCase):
    """
    Tests that need to be run with a visual browser as they require interacting
    with browser controls (alerts or onbeforeunload)
    """
    required_webdriver = 'firefox'

    def setUp(self):
        super().setUp()
        self.driver.implicitly_wait(10)

    def test_leaving_confirming_incomplete_batch(self):
        # we need firefox as this is using a native dialog
        self.login_and_go_to('New')
        self.click_done_payment(row=1)
        self.click_on_text('Home')
        self.driver.switch_to.alert.dismiss()
        self.assertEqual('New credits - Digital cashbook', self.driver.title)

    def test_leaving_not_confirming_incomplete_batch(self):
        # we need firefox as this is using a native dialog
        self.login_and_go_to('New')
        self.click_done_payment(row=1)
        self.click_on_text('Home')
        self.driver.switch_to.alert.accept()
        self.assertEqual('Digital cashbook', self.driver.title)

    def test_search_focus(self):
        self.login_and_go_to('History')
        focused_element = self.driver.find_element_by_css_selector('input:focus')
        self.assertEqual('id_search', focused_element.get_attribute('id'))
        self.type_in('id_start', 'Today')
        self.click_on_text('Search')
        focused_element = self.driver.find_element_by_css_selector('div:focus')
        self.assertEqual('error-summary', focused_element.get_attribute('class'))

    def test_go_home_with_back_button(self):
        self.login_and_go_to('New')
        self.driver.execute_script('window.history.go(-1)')
        self.assertCurrentUrl('/')


class Journeys(CashbookTestCase):
    """
    These aren't real tests but rather simulations of complex
    sessions as a real user would do. This is used to automatically
    populate analytics with semi-realistic data
    """
    required_webdriver = 'firefox'

    def click_on_checkbox(self, index):
        if index == 0:
            self.click_select_all_payments()
        else:
            self.click_done_payment(index)

    # Route: 1, 2
    def test_journey_1(self):
        self.login('test-prison-1', 'test-prison-1')
        self.click_on_text('New')
        self.click_on_checkbox(0)
        self.click_on_text('Done')
        self.assertCurrentUrl('/dashboard-batch-complete/')

    # Route: 1, 3
    def test_journey_2(self):
        self.login('test-prison-1', 'test-prison-1')
        self.click_on_text('New')
        self.click_on_text('Home')
        self.assertCurrentUrl('/dashboard-batch-discard/')

    # Route: 1, 4, 5
    def test_journey_3(self):
        self.login('test-prison-1', 'test-prison-1')
        self.click_on_text('New')
        self.click_on_checkbox(1)
        self.click_on_text('Done')
        self.click_on_text('Yes')
        self.assertCurrentUrl('/dashboard-batch-incomplete/')

    # Route: 1, 4, 6
    def test_journey_4(self):
        self.login('test-prison-1', 'test-prison-1')
        self.click_on_text('New')
        self.click_on_checkbox(1)
        self.click_on_text('Done')
        self.click_on_text('No, continue processing')
        self.assertCurrentUrl('/batch/')

    # Route 1, 7, 8
    def test_journey_5(self):
        self.login('test-prison-1', 'test-prison-1')
        self.click_on_text('New')
        self.click_on_checkbox(1)
        self.click_on_text('Home')
        self.driver.switch_to.alert.accept()
        self.assertCurrentUrl('/dashboard-batch-discard/')

    # Route 1, 7, 9
    def test_journey_6(self):
        self.login('test-prison-1', 'test-prison-1')
        self.click_on_text('New')
        self.click_on_checkbox(1)
        self.click_on_text('Home')
        self.driver.switch_to.alert.dismiss()
        self.assertCurrentUrl('/batch/')

    def test_journey_7(self):
        self.login('test-prison-1', 'test-prison-1')
        self.click_on_text('New')
        self.click_on_text('Help')
        self.click_on_text('Home')

    def test_journey_8(self):
        self.login('test-prison-1', 'test-prison-1')
        self.click_on_text('New')
        self.click_on_text('Help')
        self.click_on_text('Help')
        self.click_on_text('Home')

    def test_journey_9(self):
        self.login('test-prison-1', 'test-prison-1')
        self.click_on_text('New')
        self.click_on_text('Help')
        self.click_on_text('Help')
        self.click_on_text('Home')

    def test_journey_10(self):
        self.login('test-prison-1', 'test-prison-1')
        self.click_on_text('History')
        self.click_on_text('Home')
        self.click_on_text('History')
        self.driver.execute_script('window.history.go(-1)')
        self.click_on_text('History')


class HistoryPageTests(CashbookTestCase):
    """
    Tests for History page
    """

    def setUp(self):
        super().setUp()
        self.login_and_go_to('History')

    def get_search_button(self):
        button = self.driver.find_element_by_xpath('//input[@value="Search"]')
        self.assertIsNotNone(button)
        return button

    def test_going_to_history_page(self):
        self.assertInSource('Credit history')
        self.assertNotInSource('Intended recipient')
        self.assertNotInSource('Payments processed by')
        self.get_search_button()

    def test_do_a_search_and_make_sure_it_takes_you_back_to_history_page(self):
        self.get_search_button().click()
        self.assertCurrentUrl('/history/')

    def test_searching_history(self):
        self.assertInSource(re.compile(r'\d+ credits? received.'))
        self.type_in('id_search', '1')
        self.get_search_button().click()
        self.assertInSource(re.compile(r'Searching for “1” returned \d+ credits?.'))

    def test_help_popup(self):
        help_box_heading = self.driver.find_element_by_css_selector('.help-box-title')
        self.assertCssProperty('.help-box-contents', 'display', 'none')
        self.assertEqual('false', help_box_heading.get_attribute('aria-expanded'))
        self.click_on_text('Help')
        self.assertCssProperty('.help-box-contents', 'display', 'block')
        self.assertEqual('true', help_box_heading.get_attribute('aria-expanded'))
        self.click_on_text('Help')
        self.assertCssProperty('.help-box-contents', 'display', 'none')
        self.assertEqual('false', help_box_heading.get_attribute('aria-expanded'))


class AdminPagesTests(CashbookTestCase):
    """
    Tests for Admin pages
    """

    def setUp(self):
        super().setUp()
        self.login('admin', 'admin')
        self.click_on_text('Manage users')

    def _create_dummy_user(self, username):
        self.click_on_text('Manage users')
        self.click_on_text('Add a new user')
        self.type_in('id_username', username)
        self.type_in('id_first_name', 'Joe')
        self.type_in('id_last_name', 'Bloggs')
        self.type_in('id_email', 'a@v.com')
        self.driver.find_element_by_css_selector('form').submit()

    def test_list_page(self):
        self.assertCurrentUrl('/users/')
        self.assertInSource('Manage user accounts')
        self.assertInSource('Admin User')
        self.assertCssProperty('td.actions > div', 'margin-right', '80px')

    def test_create_user_missing_fields(self):
        self.click_on_text('Add a new user')
        self.assertInSource('Create a new user')
        self.type_in('id_username', 'dummy')
        self.driver.find_element_by_css_selector('form').submit()
        self.assertInSource('This field is required')

    def test_create_user(self):
        self._create_dummy_user('dummy')
        self.assertInSource('User account ‘dummy’ created')

    def test_delete_user(self):
        self._create_dummy_user('dummy2')
        self.click_on_text('Return to user management')
        self.get_element('//a[text()="Delete" and ancestor::tr/td[text()="dummy2"]]').click()
        self.assertInSource('Delete user account')
        self.driver.find_element_by_css_selector('form').submit()
        self.assertInSource('User account ‘dummy2’ deleted')

    def test_edit_user(self):
        self._create_dummy_user('dummy3')
        self.click_on_text('Edit this user account')
        self.type_in('id_first_name', 'Jane')
        self.driver.find_element_by_css_selector('form').submit()
        self.assertInSource('User account ‘dummy3’ edited')

    def test_edit_user_from_list(self):
        self._create_dummy_user('dummy4')
        self.click_on_text('Return to user management')
        self.get_element('//a[text()="Edit" and ancestor::tr/td[text()="dummy4"]]').click()
        self.type_in('id_first_name', 'Jane')
        self.driver.find_element_by_css_selector('form').submit()
        self.assertInSource('User account ‘dummy4’ edited')

    def test_create_two_users_same_username(self):
        self._create_dummy_user('dummy5')
        self._create_dummy_user('dummy5')
        self.assertInSource('A user with that username already exists.')
