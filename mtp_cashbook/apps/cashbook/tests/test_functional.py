import glob
import logging
import os
import re
import socket
from urllib.parse import urlparse
import unittest

from django.conf import settings
from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

logger = logging.getLogger('mtp')


@unittest.skipUnless('RUN_FUNCTIONAL_TESTS' in os.environ, 'functional tests are disabled')
class FunctionalTestCase(LiveServerTestCase):
    """
    Base class to define common methods to test subclasses below
    """

    @classmethod
    def _databases_names(cls, include_mirrors=True):
        # this app has no databases
        return []

    def setUp(self):
        self.load_test_data()
        web_driver = os.environ.get('WEBDRIVER', 'phantomjs')
        if web_driver == 'firefox':
            fp = webdriver.FirefoxProfile()
            fp.set_preference('browser.startup.homepage', 'about:blank')
            fp.set_preference('startup.homepage_welcome_url', 'about:blank')
            fp.set_preference('startup.homepage_welcome_url.additional', 'about:blank')
            self.driver = webdriver.Firefox(firefox_profile=fp)
        elif web_driver == 'chrome':
            paths = glob.glob('node_modules/selenium-standalone/.selenium/chromedriver/*-chromedriver')
            paths = filter(lambda path: os.path.isfile(path) and os.access(path, os.X_OK),
                           paths)
            try:
                self.driver = webdriver.Chrome(executable_path=next(paths))
            except StopIteration:
                self.fail('Cannot find Chrome driver')
        else:
            path = './node_modules/phantomjs/lib/phantom/bin/phantomjs'
            self.driver = webdriver.PhantomJS(executable_path=path)

        self.driver.set_window_size(1000, 1000)
        self.driver.set_window_position(0, 0)

    def tearDown(self):
        self.driver.quit()

    def load_test_data(self):
        logger.info('Reloading test data')
        try:
            with socket.socket() as sock:
                sock.connect((
                    urlparse(settings.API_URL).netloc.split(':')[0],
                    os.environ.get('CONTROLLER_PORT', 8800)
                ))
                sock.sendall(b'load_test_data')
                response = sock.recv(1024).strip()
            if response != b'done':
                logger.error('Test data not reloaded!')
        except OSError:
            logger.exception('Error communicating with test server controller socket')

    def login(self, username, password):
        self.driver.get(self.live_server_url)
        login_field = self.driver.find_element_by_id('id_username')
        login_field.send_keys(username)
        password_field = self.driver.find_element_by_id('id_password')
        password_field.send_keys(password + Keys.RETURN)

    def login_and_go_to(self, link_text):
        self.login('test-prison-1', 'test-prison-1')
        self.driver.find_element_by_partial_link_text(link_text).click()

    def click_checkbox(self, index):
        self.driver.find_elements_by_xpath('//input[@type="checkbox"]')[index].click()

    def click_on(self, text):
        self.driver.find_element_by_xpath(
            '//*[text() = "' + text + '"] | '
            '//input[@type="submit" and @value="' + text + '"]'
        ).click()

    def scroll_to_top(self):
        self.driver.execute_script('window.scrollTo(0, 0);')

    def scroll_to_bottom(self):
        self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')

    def type_in(self, element_id, text):
        self.driver.find_element_by_id(element_id).send_keys(text)

    def assertInSource(self, search):  # noqa
        if hasattr(search, 'search'):
            self.assertTrue(search.search(self.driver.page_source))
        else:
            self.assertIn(search, self.driver.page_source)

    def assertNotInSource(self, search):  # noqa
        if hasattr(search, 'search'):
            self.assertFalse(search.search(self.driver.page_source))
        else:
            self.assertNotIn(search, self.driver.page_source)


class LoginTests(FunctionalTestCase):
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


class LockedPaymentsPageTests(FunctionalTestCase):
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


class NewPaymentsPageTests(FunctionalTestCase):
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
        self.driver.find_element_by_xpath('//input[@type="checkbox" and @data-amount]').click()
        self.driver.find_element_by_xpath('//button[text()="Done"]').click()
        self.assertIsNotNone(self.driver.find_element_by_xpath(
            '//div[@class="Dialog-inner"]/h3[text()="Are you sure?"]'
        ))

    def test_submitting_and_confirming_partial_batch(self):
        self.driver.find_element_by_xpath('//input[@type="checkbox" and @data-amount][1]').click()
        self.driver.find_element_by_xpath('//button[text()="Done"]').click()
        self.driver.find_element_by_xpath('//div[@class="Dialog-inner"]/*[text()="Yes"]').click()
        self.assertInSource('You’ve credited 1 payment to NOMIS.')
        self.assertEqual('Digital cashbook', self.driver.title)

    def test_submitting_and_not_confirming_partial_batch(self):
        self.driver.find_element_by_xpath('//input[@type="checkbox" and @data-amount][1]').click()
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
        help_box_button = self.driver.find_element_by_css_selector('.help-box h3')
        self.assertEqual('none', help_box_contents.value_of_css_property('display'))
        help_box_button.click()
        self.assertEqual('block', help_box_contents.value_of_css_property('display'))
        help_box_button.click()
        self.assertEqual('none', help_box_contents.value_of_css_property('display'))

    def test_go_back_home(self):
        self.driver.find_element_by_link_text('Home').click()
        self.assertEqual('Digital cashbook', self.driver.title)

    def test_submitting_complete_batch(self):
        self.driver.find_element_by_xpath('//input[@type="checkbox"][1]').click()
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


@unittest.skipUnless(os.environ.get('WEBDRIVER') == 'firefox', 'visual tests require firefox web driver')
class VisualTests(FunctionalTestCase):
    """
    Tests that need to be run with a visual browser as they require interacting
    with browser controls (alerts or onbeforeunload)
    """

    def setUp(self):
        super().setUp()
        self.driver.implicitly_wait(10)

    def test_leaving_confirming_incomplete_batch(self):
        # we need firefox as this is using a native dialog
        self.login_and_go_to('New')
        self.driver.find_element_by_xpath('//input[@type="checkbox" and @data-amount][1]').click()
        self.driver.find_element_by_link_text('Home').click()
        self.driver.switch_to.alert.dismiss()
        self.assertEqual('New credits - Digital cashbook', self.driver.title)

    def test_leaving_not_confirming_incomplete_batch(self):
        # we need firefox as this is using a native dialog
        self.login_and_go_to('New')
        self.driver.find_element_by_xpath('//input[@type="checkbox" and @data-amount][1]').click()
        self.driver.find_element_by_link_text('Home').click()
        self.driver.switch_to.alert.accept()
        self.assertEqual('Digital cashbook', self.driver.title)

    def test_search_focus(self):
        self.login_and_go_to('History')
        focused_element = self.driver.find_element_by_css_selector('input:focus')
        self.assertEqual('id_search', focused_element.get_attribute('id'))
        self.driver.find_element_by_id('id_start').clear()
        self.click_on('Search')
        focused_element = self.driver.find_element_by_css_selector('div:focus')
        self.assertEqual('error-summary', focused_element.get_attribute('class'))


@unittest.skipUnless(os.environ.get('WEBDRIVER') == 'firefox', 'visual tests require firefox web driver')
class Journeys(FunctionalTestCase):
    """
    These aren't real tests but rather simulations of complex
    sessions as a real user would do. This is used to automatically
    populate analytics with semi-realistic data
    """

    def test_journey_1(self):
        self.login('test-prison-1', 'bad-password')
        self.login('test-prison-1', 'bad-password-again')
        self.login('test-prison-1', 'test-prison-1')
        self.click_on('New')
        self.click_on('How to process credits in NOMIS')
        self.click_on('How to process credits in NOMIS')
        self.click_on('Done')
        self.click_checkbox(2)
        self.scroll_to_top()
        self.click_on('Done')
        self.click_on('No, continue processing')
        self.click_on('Done')
        self.click_on('Yes')
        self.click_on('History')
        self.scroll_to_bottom()
        self.click_on('Print these payments')
        self.click_on('Cancel')
        self.scroll_to_top()
        self.click_on('Sign out')

    def test_journey_2(self):
        self.login('test-prison-1', 'test-prison-1')
        self.click_on('History')
        self.type_in('id_search', 'e')
        self.type_in('id_start', '15-01-16')
        self.click_on('Search')
        self.type_in('id_start', '15/01/2016')
        self.click_on('Search')
        self.click_on('Home')

    def test_journey_3(self):
        self.login('test-prison-1', 'test-prison-1')
        self.click_on('New')
        self.click_checkbox(1)
        self.click_on('Home')
        self.driver.switch_to.alert.dismiss()
        self.click_checkbox(0)
        self.click_on('Done')
        self.click_on('In progress')
        self.click_on('Sign out')

    def test_journey_4(self):
        self.login('test-prison-1', 'test-prison-1')
        self.click_on('New')
        self.click_checkbox(1)
        self.click_on('Home')
        self.driver.switch_to.alert.accept()
        self.click_on('History')
        self.click_on('Home')
        self.click_on('Sign out')

    def test_journey_5(self):
        self.login('test-prison-1', 'test-prison-1')
        self.click_on('New')
        self.click_checkbox(1)
        self.scroll_to_top()
        self.click_on('Done')
        self.click_on('Sign out')


class HistoryPageTests(FunctionalTestCase):
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
        self.assertInSource(re.compile(r'Showing \d+ payments.'))
        self.type_in('id_search', '1')
        self.get_search_button().click()
        self.assertInSource(re.compile(r'Searching for “1” returned \d+ payments.'))
