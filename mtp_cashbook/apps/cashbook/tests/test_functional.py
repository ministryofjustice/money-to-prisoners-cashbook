import os
import unittest

from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.keys import Keys


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
        path = './node_modules/phantomjs/lib/phantom/bin/phantomjs'
        self.driver = webdriver.PhantomJS(executable_path=path)

    def tearDown(self):
        self.driver.quit()

    def login(self, username, password):
        self.driver.get(self.live_server_url)
        login_field = self.driver.find_element_by_id('id_username')
        login_field.send_keys(username)
        password_field = self.driver.find_element_by_id('id_password')
        password_field.send_keys(password + Keys.RETURN)

    def login_and_go_to(self, link_text):
        self.login('test-prison-1', 'test-prison-1')
        self.driver.find_element_by_partial_link_text(link_text).click()


class LoginTests(FunctionalTestCase):
    """
    Tests for Login page
    """

    def test_title(self):
        self.driver.get(self.live_server_url)
        heading = self.driver.find_element_by_tag_name('h1')
        self.assertEquals('Money sent to prisoners', heading.text)
        self.assertEquals('32px', heading.value_of_css_property('font-size'))

    def test_bad_login(self):
        self.login('test-prison-1', 'bad-password')
        self.assertIn('There was a problem submitting the form',
                      self.driver.page_source)

    def test_good_login(self):
        self.login('test-prison-1', 'test-prison-1')
        self.assertEquals(self.driver.current_url, self.live_server_url + '/')
        self.assertIn('Credits to process', self.driver.page_source)

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
        self.assertIn('Credits in progress', self.driver.page_source)
        self.assertIn('Staff name', self.driver.page_source)
        self.assertIn('Time in progress', self.driver.page_source)


class NewPaymentsPageTests(FunctionalTestCase):
    """
    Tests for New Payments page
    """

    def setUp(self):
        super().setUp()
        self.login_and_go_to('New')

    def test_going_to_the_credits_page(self):
        self.assertIn('New credits', self.driver.page_source)
        self.assertIn('Control total', self.driver.page_source)

    def test_submitting_payments_credited(self):
        self.driver.find_element_by_xpath('//input[@type="checkbox"]').click()
        self.driver.find_element_by_xpath('//button[text()="Done"]').click()
        self.assertIsNotNone(self.driver.find_element_by_xpath('//div[@class="Dialog-inner"]/h3[text()="Are you sure?"]'))

    def test_submitting_and_confirming_payments_credited(self):
        self.driver.find_element_by_xpath('//input[@type="checkbox" and @data-amount]').click()
        self.driver.find_element_by_xpath('//button[text()="Done"]').click()
        self.assertIn('You\'ve credited 1 payment to NOMIS.', self.driver.page_source)

    def test_clicking_done_with_no_payments_credited(self):
        self.driver.find_element_by_xpath('//button[text()="Done"]').click()
        self.assertIsNotNone(self.driver.find_element_by_xpath('//div[@class="error-summary"]/h1[text()="You have not ticked any credits"]'))

    def test_printing(self):
        self.driver.find_element_by_link_text('Print these payments').click()
        self.assertIsNotNone(self.driver.find_element_by_xpath('//div[@class="Dialog-inner"]/h3[text()="Do you need to print?"]'))


class HistoryPageTests(FunctionalTestCase):
    """
    Tests for History page
    """

    def setUp(self):
        super().setUp()
        self.login_and_go_to('History')

    def test_going_to_history_page(self):
        self.assertIn('Credit history', self.driver.page_source)
        self.assertIsNotNone(self.driver.find_element_by_xpath('//input[@value="Search"]'))
        self.assertNotIn('Payments processed by', self.driver.page_source)

    def test_do_a_search_and_make_sure_it_takes_you_back_to_history_page(self):
        self.driver.find_element_by_xpath('//input[@value="Search"]').click()
        self.assertEqual(self.driver.current_url.split('?')[0], self.live_server_url + '/history/')