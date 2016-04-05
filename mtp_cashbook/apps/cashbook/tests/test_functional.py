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
        self.assertEqual('48px', heading.value_of_css_property('font-size'))

    def test_bad_login(self):
        self.login('test-prison-1', 'bad-password')
        self.assertInSource('There was a problem submitting the form')

    def test_good_login(self):
        self.login('test-prison-1', 'test-prison-1')
        self.assertEqual(self.driver.current_url, self.live_server_url + '/')
        self.assertInSource('Credits to process')

    def test_logout(self):
        self.login('test-prison-1', 'test-prison-1')
        self.driver.find_element_by_link_text('Sign out').click()
        self.assertEqual(self.driver.current_url.split('?')[0], self.live_server_url + '/login/')


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
        help_box_contents = self.driver.find_element_by_css_selector('.help-box-contents')
        help_box_heading = self.driver.find_element_by_css_selector('.help-box-title')
        help_box_link = self.driver.find_element_by_css_selector('.help-box-title a')
        self.assertEqual('none', help_box_contents.value_of_css_property('display'))
        self.assertEqual('false', help_box_heading.get_attribute('aria-expanded'))
        help_box_link.click()
        self.assertEqual('block', help_box_contents.value_of_css_property('display'))
        self.assertEqual('true', help_box_heading.get_attribute('aria-expanded'))
        help_box_link.click()
        self.assertEqual('none', help_box_contents.value_of_css_property('display'))
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
        self.driver.find_element_by_xpath('//button[text()="Done"]').click()
        self.assertIsNotNone(self.driver.find_element_by_xpath(
            '//div[@class="Dialog-inner"]/h3[text()="Are you sure?"]'
        ))

    def test_submitting_and_confirming_partial_batch(self):
        self.click_done_payment(row=1)
        self.driver.find_element_by_xpath('//button[text()="Done"]').click()
        self.driver.find_element_by_xpath('//div[@class="Dialog-inner"]/*[text()="Yes"]').click()
        self.assertInSource('You’ve credited 1 payment to NOMIS.')
        self.assertEqual('Digital cashbook', self.driver.title)

    def test_submitting_and_not_confirming_partial_batch(self):
        self.click_done_payment(row=1)
        self.driver.find_element_by_xpath('//button[text()="Done"]').click()
        self.driver.find_element_by_xpath('//div[@class="Dialog-inner"]/*[text()="No, continue processing"]').click()
        self.assertEqual('New credits - Digital cashbook', self.driver.title)

    def test_clicking_done_with_no_payments_credited(self):
        self.driver.find_element_by_xpath('//button[text()="Done"]').click()
        self.assertIsNotNone(self.driver.find_element_by_xpath(
            '//div[@class="error-summary"]/h1[text()="You have not ticked any credits"]'
        ))

    def test_printing(self):
        self.driver.find_element_by_link_text('Print these payments').click()
        self.assertIsNotNone(self.driver.find_element_by_xpath(
            '//div[@class="Dialog-inner"]/h3[text()="Do you need to print?"]'
        ))

    def test_help_popup(self):
        help_box_contents = self.driver.find_element_by_css_selector('.help-box-contents')
        help_box_heading = self.driver.find_element_by_css_selector('.help-box-title')
        help_box_link = self.driver.find_element_by_css_selector('.help-box-title a')
        self.assertEqual('none', help_box_contents.value_of_css_property('display'))
        self.assertEqual('false', help_box_heading.get_attribute('aria-expanded'))
        help_box_link.click()
        self.assertEqual('block', help_box_contents.value_of_css_property('display'))
        self.assertEqual('true', help_box_heading.get_attribute('aria-expanded'))
        help_box_link.click()
        self.assertEqual('none', help_box_contents.value_of_css_property('display'))
        self.assertEqual('false', help_box_heading.get_attribute('aria-expanded'))

    def test_go_back_home(self):
        self.driver.find_element_by_link_text('Home').click()
        self.assertEqual('Digital cashbook', self.driver.title)
        self.assertEqual(self.driver.current_url, self.live_server_url + '/dashboard-batch-discard/')

    def test_submitting_complete_batch(self):
        self.click_select_all_payments()
        self.driver.find_element_by_xpath('//button[text()="Done"]').click()
        self.assertEqual('Digital cashbook', self.driver.title)
        self.assertInSource('You’ve credited')

    def test_checkboxes_style(self):
        # Regression tests for https://www.pivotaltracker.com/story/show/115328657
        self.driver.find_element_by_link_text('Print these payments').click()
        remember_checkbox = self.driver.find_element_by_xpath('//label[@for="remove-print-prompt"]')
        self.assertEqual('0px 10%', remember_checkbox.value_of_css_property('background-position'))
        self.driver.find_element_by_link_text('close').click()
        select_all_checkbox = self.driver.find_element_by_xpath('//label[@for="select-all-header"][1]')
        self.assertEqual('100% 10%', select_all_checkbox.value_of_css_property('background-position'))


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
        self.driver.find_element_by_link_text('Home').click()
        self.driver.switch_to.alert.dismiss()
        self.assertEqual('New credits - Digital cashbook', self.driver.title)

    def test_leaving_not_confirming_incomplete_batch(self):
        # we need firefox as this is using a native dialog
        self.login_and_go_to('New')
        self.click_done_payment(row=1)
        self.driver.find_element_by_link_text('Home').click()
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
        self.assertEqual(self.driver.current_url, self.live_server_url + '/')


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
        self.assertEqual(self.driver.current_url.split('?')[0], self.live_server_url + '/history/')

    def test_searching_history(self):
        self.assertInSource(re.compile(r'\d+ credits? received.'))
        self.type_in('id_search', '1')
        self.get_search_button().click()
        self.assertInSource(re.compile(r'Searching for “1” returned \d+ credits?.'))

    def test_help_popup(self):
        help_box_contents = self.driver.find_element_by_css_selector('.help-box-contents')
        help_box_heading = self.driver.find_element_by_css_selector('.help-box-title')
        help_box_link = self.driver.find_element_by_css_selector('.help-box-title a')
        self.assertEqual('none', help_box_contents.value_of_css_property('display'))
        self.assertEqual('false', help_box_heading.get_attribute('aria-expanded'))
        help_box_link.click()
        self.assertEqual('block', help_box_contents.value_of_css_property('display'))
        self.assertEqual('true', help_box_heading.get_attribute('aria-expanded'))
        help_box_link.click()
        self.assertEqual('none', help_box_contents.value_of_css_property('display'))
        self.assertEqual('false', help_box_heading.get_attribute('aria-expanded'))
