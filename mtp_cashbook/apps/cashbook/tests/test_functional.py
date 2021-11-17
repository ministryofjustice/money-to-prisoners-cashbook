from datetime import date
import logging
import os

from mtp_common.test_utils import silence_logger
from mtp_common.test_utils.functional_tests import FunctionalTestCase
from selenium.common.exceptions import NoSuchElementException

logger = logging.getLogger('mtp')


class CashbookTestCase(FunctionalTestCase):
    """
    Base class to define common methods to test subclasses below
    """
    auto_load_test_data = True
    accessibility_scope_selector = '#content'
    username = 'test-hmp-leeds'

    def load_test_data(self):
        with silence_logger(name='mtp', level=logging.WARNING):
            super().load_test_data(command=b'load_nomis_test_data')

    def login(self, username, password, url=None,
              username_field='id_username', password_field='id_password'):
        """
        Fill in login form
        """
        super().login(username, password, url=url, username_field=username_field, password_field=password_field)
        try:
            self.get_element('//button[@name="read_briefing"]').click()
        except NoSuchElementException:
            pass

    def click_logout(self):
        """
        Finds and clicks the log-out link
        """
        self.driver.find_element_by_link_text('Sign out').click()

    def login_and_go_to(self, link_text, substring=False):
        self.login(self.username, self.username)
        self.click_on_link('Digital cashbook')
        if substring:
            self.click_on_text_substring(link_text)
        else:
            self.click_on_text(link_text)

    def select_all_credits(self):
        self.get_element('//label[@for="select-all-header"]').click()

    def select_first_credit(self):
        xpath = '//input[@type="checkbox" and @data-amount][1]'
        checkbox_id = self.get_element(xpath).get_attribute('id')
        self.get_element('//label[@for="%s"]' % checkbox_id).click()

    def assertShowingView(self, view_name):  # noqa: N802
        self.assertInSource('<!--[%s]-->' % view_name)

    def click_on_link(self, text):
        self.driver.find_element_by_link_text(text).click()


class LoginTests(CashbookTestCase):
    """
    Tests for Login page
    """

    def test_title(self):
        self.driver.get(self.live_server_url + '/en-gb/')
        heading = self.driver.find_element_by_tag_name('h1')
        self.assertEqual('Process money in and out of your prison', heading.text)

    def test_bad_login(self):
        self.login('test-hmp-leeds', 'bad-password')
        self.assertInSource('There was a problem')
        self.assertShowingView('login')

    def test_good_login(self):
        self.login('test-hmp-leeds', 'test-hmp-leeds')
        self.assertCurrentUrl('/en-gb/')
        self.assertShowingView('home')

    def test_good_login_without_case_sensitivity(self):
        self.login('test-HMP-leeds', 'test-hmp-leeds')
        self.assertCurrentUrl('/en-gb/')
        self.assertShowingView('home')

    def test_logout(self):
        self.login('test-hmp-leeds', 'test-hmp-leeds')
        self.click_logout()
        self.assertCurrentUrl('/en-gb/login/')
        self.assertShowingView('login')


class NewCreditsPageTests(CashbookTestCase):
    """
    Tests for new credits page
    """

    def setUp(self):
        super().setUp()
        self.login_and_go_to('New credits')

    def test_going_to_the_credits_page(self):
        self.assertShowingView('new-credits')

    def test_submitting_partial_batch(self):
        self.select_first_credit()
        self.click_on_text('Credit to NOMIS')
        self.assertIsNotNone(self.driver.find_element_by_xpath(
            '//div[contains(@class, "mtp-dialogue")]'
            '/header[contains(text(), "Do you want to submit only the selected credits?")]'
        ))

    def test_submitting_and_not_confirming_partial_batch(self):
        self.select_first_credit()
        self.click_on_text('Credit to NOMIS')
        self.driver.find_element_by_xpath(
            '//a[normalize-space(text()) = "No, continue processing"]'
        ).click()
        self.assertEqual('New credits – Digital cashbook', self.driver.title)

    @silence_logger(name='mtp', level=logging.WARNING)
    def test_submitting_and_confirming_partial_batch(self):
        self.select_first_credit()
        self.click_on_text('Credit to NOMIS')
        self.get_element('//button[@name="submit_new" and @value="override"]').click()
        if os.environ.get('DJANGO_TEST_REMOTE_INTEGRATION_URL', None):
            try:
                self.assertInSource('Digital cashbook is crediting to NOMIS')
                self.driver.implicitly_wait(15)
            except AssertionError:
                self.assertInSource('Digital cashbook has finished crediting to NOMIS')
            self.click_on_text('Continue')
        self.assertInSource('1 credit sent to NOMIS')

    @silence_logger(name='mtp', level=logging.WARNING)
    def test_submitting_complete_batch(self):
        self.select_all_credits()
        self.click_on_text('Credit to NOMIS')
        if os.environ.get('DJANGO_TEST_REMOTE_INTEGRATION_URL', None):
            try:
                self.assertInSource('Digital cashbook is crediting to NOMIS')
                self.driver.implicitly_wait(20)
            except AssertionError:
                self.assertInSource('Digital cashbook has finished crediting to NOMIS')
            self.click_on_text('Continue')
        self.assertInSource('credits sent to NOMIS')


class ProcessedCreditsPageTests(CashbookTestCase):
    """
    Tests for processed credits page
    """

    def setUp(self):
        super().setUp()
        self.login_and_go_to('Processed credits')

    def get_filter_button(self):
        button = self.driver.find_element_by_xpath('//input[@value="Filter list"]')
        self.assertIsNotNone(button)
        return button

    def test_going_to_processed_credits_page(self):
        self.assertInSource('Processed credits')
        self.get_filter_button()

    def test_do_filter_and_make_sure_it_takes_you_back_to_processed_page(self):
        self.get_filter_button().click()
        self.assertCurrentUrl('/en-gb/processed/')

    def test_filtering_processed_credits(self):
        self.type_in('id_start', date.today().isoformat())
        self.get_filter_button().click()
        self.assertCurrentUrl('/en-gb/processed/')
        self.assertNotInSource('There was a problem')


class SearchCreditsTests(CashbookTestCase):
    """
    Tests for search credits
    """

    def setUp(self):
        super().setUp()
        self.login_and_go_to('New credits')

    def get_search_button(self):
        button = self.driver.find_element_by_xpath('//button[text()="Search"]')
        self.assertIsNotNone(button)
        return button

    def test_search_credits(self):
        search_term = 'Smith'
        self.type_in('id_search', search_term)
        self.get_search_button().click()
        self.assertCurrentUrl('/en-gb/search/')
        self.assertInSource('Search for “%s”' % search_term)


@silence_logger(name='mtp', level=logging.WARNING)
class AdminPagesTests(CashbookTestCase):
    """
    Tests for Admin pages
    """
    username = 'test-hmp-leeds-ua'

    def setUp(self):
        super().setUp()
        self.login_and_go_to('Manage users')

    def _create_dummy_user(self, username):
        self.click_on_text('Manage users')
        self.click_on_text('Add a new user')
        self.type_in('id_username', username)
        self.type_in('id_first_name', 'Joe')
        self.type_in('id_last_name', 'Bloggs')
        self.type_in('id_email', 'joe@mtp.local')
        self.driver.find_element_by_css_selector('form').submit()

    def test_list_page(self):
        self.assertCurrentUrl('/en-gb/users/')
        self.assertInSource('Manage user accounts')
        self.assertInSource('Prison 1 Clerk')

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
        self.get_element('//div[position()=2]/a[ancestor::tr/td[text()="dummy2"]]').click()
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
        self.assertInSource('That username already exists')
