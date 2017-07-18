import logging
import re

from mtp_common.test_utils import silence_logger
from mtp_common.test_utils.functional_tests import FunctionalTestCase

from cashbook.tests.test_nomis_views import override_nomis_settings

logger = logging.getLogger('mtp')


@override_nomis_settings
class CashbookTestCase(FunctionalTestCase):
    """
    Base class to define common methods to test subclasses below
    """
    auto_load_test_data = True
    accessibility_scope_selector = '#content'

    def load_test_data(self):
        with silence_logger(name='mtp', level=logging.WARNING):
            super().load_test_data()

    def login(self, *args, **kwargs):
        kwargs.setdefault('url', self.live_server_url + '/en-gb/')
        super().login(*args, **kwargs)

    def click_logout(self):
        """
        Finds and clicks the log-out link
        NB: assumed to be last link; can't use click_on_text('Sign out [name]') due to whitespace
        """
        self.driver.find_element_by_css_selector('#proposition-links li:last-child a').click()

    def login_and_go_to(self, link_text, substring=False):
        self.login('test-prison-1', 'test-prison-1')
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

    def assertShowingView(self, view_name):  # noqa
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
        self.assertEqual('Digital cashbook\nSign in', heading.text)

    def test_bad_login(self):
        self.login('test-prison-1', 'bad-password')
        self.assertInSource('There was a problem')
        self.assertShowingView('login')

    def test_good_login(self):
        self.login('test-prison-1', 'test-prison-1')
        self.assertCurrentUrl('/en-gb/')
        self.assertShowingView('dashboard')

    def test_good_login_without_case_sensitivity(self):
        self.login('Test-PRISON-1', 'test-prison-1')
        self.assertCurrentUrl('/en-gb/')
        self.assertShowingView('dashboard')

    def test_logout(self):
        self.login('test-prison-1', 'test-prison-1')
        self.click_logout()
        self.assertCurrentUrl('/en-gb/login/')
        self.assertShowingView('login')


class InProgressPageTests(CashbookTestCase):
    """
    Tests for locked credits page
    """

    def setUp(self):
        super().setUp()
        self.login_and_go_to('Return these to new credits')

    def test_going_to_the_locked_credits_page(self):
        self.assertInSource('Currently being entered into NOMIS')
        self.assertInSource('Staff name')
        self.assertInSource('Time in progress')

    @silence_logger(name='mtp', level=logging.WARNING)
    def test_releasing_credits(self):
        self.get_element('//tbody//input[@type="checkbox"][1]/following-sibling::label').click()
        self.click_on_text('Return these to new credits')
        self.assertCurrentUrl('/en-gb/dashboard-unlocked-payments/')
        self.assertInSource('You have now returned')

    def test_help_popup(self):
        help_box_heading = self.driver.find_element_by_css_selector('.mtp-disclosure')
        self.assertCssProperty('.mtp-disclosure__contents', 'display', 'none')
        self.assertEqual('false', help_box_heading.get_attribute('aria-expanded'))
        self.click_on_link('Help')
        self.assertCssProperty('.mtp-disclosure__contents', 'display', 'block')
        self.assertEqual('true', help_box_heading.get_attribute('aria-expanded'))
        self.click_on_link('Help')
        self.assertCssProperty('.mtp-disclosure__contents', 'display', 'none')
        self.assertEqual('false', help_box_heading.get_attribute('aria-expanded'))


class NewCreditsPageTests(CashbookTestCase):
    """
    Tests for new credits page
    """

    def setUp(self):
        super().setUp()
        self.login_and_go_to('Enter next', substring=True)

    def test_going_to_the_credits_page(self):
        self.assertInSource('New credits')
        self.assertInSource('Control total')

    def test_submitting_credits_credited(self):
        self.select_first_credit()
        self.click_on_text('Confirm entered in NOMIS')
        self.assertIsNotNone(self.driver.find_element_by_xpath(
            '//div[contains(@class, "mtp-dialogue")]'
            '/header[contains(text(), "Do you want to submit only the selected credits?")]'
        ))

    @silence_logger(name='mtp', level=logging.WARNING)
    def test_submitting_and_confirming_partial_batch(self):
        self.select_first_credit()
        self.click_on_text('Confirm entered in NOMIS')
        self.click_on_text('Yes')
        self.assertInSource('You’ve added 1 credit to NOMIS.')
        self.assertEqual('Digital cashbook', self.driver.title)

    def test_submitting_and_not_confirming_partial_batch(self):
        self.select_first_credit()
        self.click_on_text('Confirm entered in NOMIS')
        self.click_on_text('No, continue processing')
        self.assertEqual('New credits – Digital cashbook', self.driver.title)

    def test_printing(self):
        self.click_on_text('Print these credits')
        self.assertIsNotNone(self.driver.find_element_by_xpath(
            '//div[contains(@class, "mtp-dialogue")]'
            '/header[contains(text(), "Do you need to print?")]'
        ))

    def test_help_popup(self):
        help_box_heading = self.driver.find_element_by_css_selector('.mtp-disclosure')
        self.assertCssProperty('.mtp-disclosure__contents', 'display', 'none')
        self.assertEqual('false', help_box_heading.get_attribute('aria-expanded'))
        self.click_on_link('How to use this with NOMIS')
        self.assertCssProperty('.mtp-disclosure__contents', 'display', 'block')
        self.assertEqual('true', help_box_heading.get_attribute('aria-expanded'))
        self.click_on_link('How to use this with NOMIS')
        self.assertCssProperty('.mtp-disclosure__contents', 'display', 'none')
        self.assertEqual('false', help_box_heading.get_attribute('aria-expanded'))

    def test_go_back_home(self):
        self.click_on_text('Home')
        self.assertEqual('Digital cashbook', self.driver.title)
        self.assertCurrentUrl('/en-gb/dashboard-batch-discard/')

    @silence_logger(name='mtp', level=logging.WARNING)
    def test_submitting_complete_batch(self):
        self.select_all_credits()
        self.click_on_text('Confirm entered in NOMIS')
        self.assertEqual('Digital cashbook', self.driver.title)
        self.assertInSource('You’ve added')


class VisualTests(CashbookTestCase):
    """
    Tests that need to be run with a visual browser as they require interacting
    with browser controls (alerts or onbeforeunload)
    """
    required_webdrivers = ('chrome', 'firefox')

    def setUp(self):
        super().setUp()
        self.driver.implicitly_wait(10)

    def test_leaving_confirming_incomplete_batch(self):
        # we need firefox as this is using a native dialog
        self.login_and_go_to('Enter next', substring=True)
        self.select_first_credit()
        self.click_on_text('Home')
        self.driver.switch_to.alert.dismiss()
        self.assertEqual('New credits - Digital cashbook', self.driver.title)

    def test_leaving_not_confirming_incomplete_batch(self):
        # we need firefox as this is using a native dialog
        self.login_and_go_to('Enter next', substring=True)
        self.select_first_credit()
        self.click_on_text('Home')
        self.driver.switch_to.alert.accept()
        self.assertEqual('Digital cashbook', self.driver.title)

    def test_search_focus(self):
        def is_search_input_focused():
            element_tag, element_id = self.driver.execute_script('return [document.activeElement.tagName, '
                                                                 'document.activeElement.id];')
            return element_tag == 'INPUT' and element_id == 'id_search'

        self.login_and_go_to('View all credits')
        self.assertTrue(is_search_input_focused())
        self.type_in('id_start', 'Today')
        self.click_on_text('Search')
        self.assertFalse(is_search_input_focused())

    def test_go_home_with_back_button(self):
        self.login_and_go_to('Enter next', substring=True)
        self.driver.execute_script('window.history.go(-1)')
        self.assertCurrentUrl('/en-gb/')


@silence_logger(name='mtp', level=logging.WARNING)
class Journeys(CashbookTestCase):
    """
    These aren't real tests but rather simulations of complex
    sessions as a real user would do. This is used to automatically
    populate analytics with semi-realistic data
    """
    required_webdrivers = ('chrome', 'firefox')

    # Route: 1, 2
    def test_journey_1(self):
        self.login('test-prison-1', 'test-prison-1')
        self.click_on_text_substring('Enter next')
        self.select_all_credits()
        self.click_on_text('Confirm entered in NOMIS')
        self.assertCurrentUrl('/en-gb/dashboard-batch-complete/')

    # Route: 1, 3
    def test_journey_2(self):
        self.login('test-prison-1', 'test-prison-1')
        self.click_on_text_substring('Enter next')
        self.click_on_text('Home')
        self.assertCurrentUrl('/en-gb/dashboard-batch-discard/')

    # Route: 1, 4, 5
    def test_journey_3(self):
        self.login('test-prison-1', 'test-prison-1')
        self.click_on_text_substring('Enter next')
        self.select_first_credit()
        self.click_on_text('Confirm entered in NOMIS')
        self.click_on_text('Yes')
        self.assertCurrentUrl('/en-gb/dashboard-batch-incomplete/')

    # Route: 1, 4, 6
    def test_journey_4(self):
        self.login('test-prison-1', 'test-prison-1')
        self.click_on_text_substring('Enter next')
        self.select_first_credit()
        self.click_on_text('Confirm entered in NOMIS')
        self.click_on_text('No, continue processing')
        self.assertCurrentUrl('/en-gb/batch/')

    # Route 1, 7, 8
    def test_journey_5(self):
        self.login('test-prison-1', 'test-prison-1')
        self.click_on_text_substring('Enter next')
        self.select_first_credit()
        self.click_on_text('Home')
        self.driver.switch_to.alert.accept()
        self.assertCurrentUrl('/en-gb/dashboard-batch-discard/')

    # Route 1, 7, 9
    def test_journey_6(self):
        self.login('test-prison-1', 'test-prison-1')
        self.click_on_text_substring('Enter next')
        self.select_first_credit()
        self.click_on_text('Home')
        self.driver.switch_to.alert.dismiss()
        self.assertCurrentUrl('/en-gb/batch/')

    def test_journey_7(self):
        self.login('test-prison-1', 'test-prison-1')
        self.click_on_text_substring('Enter next')
        self.click_on_text('How to use this with NOMIS')
        self.click_on_text('Home')

    def test_journey_8(self):
        self.login('test-prison-1', 'test-prison-1')
        self.click_on_text_substring('Enter next')
        self.click_on_text('How to use this with NOMIS')
        self.click_on_text('How to use this with NOMIS')
        self.click_on_text('Home')

    def test_journey_9(self):
        self.login('test-prison-1', 'test-prison-1')
        self.click_on_text_substring('Enter next')
        self.click_on_text('How to use this with NOMIS')
        self.click_on_text('How to use this with NOMIS')
        self.click_on_text('Home')

    def test_journey_10(self):
        self.login('test-prison-1', 'test-prison-1')
        self.click_on_text_substring('Enter next')
        self.click_on_text('Home')
        self.click_logout()

    def test_journey_11(self):
        self.login('test-prison-1', 'test-prison-1')
        self.click_on_text_substring('Enter next')
        self.driver.execute_script('window.history.go(-1)')
        self.click_logout()

    def test_journey_12(self):
        self.login('test-prison-1', 'test-prison-1')
        self.click_on_text('Return these to new credits')
        self.click_on_text('Release')

    def test_journey_13(self):
        self.login('test-prison-1', 'test-prison-1')
        self.click_on_text('Return these to new credits')
        self.get_element('//tbody//input[@type="checkbox"][1]/following-sibling::label').click()
        self.click_on_text('Release')


class HistoryPageTests(CashbookTestCase):
    """
    Tests for History page
    """

    def setUp(self):
        super().setUp()
        self.login_and_go_to('View all credits')

    def get_search_button(self):
        button = self.driver.find_element_by_xpath('//input[@value="Search"]')
        self.assertIsNotNone(button)
        return button

    def test_going_to_history_page(self):
        self.assertInSource('All credits')
        self.get_search_button()

    def test_do_a_search_and_make_sure_it_takes_you_back_to_history_page(self):
        self.get_search_button().click()
        self.assertCurrentUrl('/en-gb/history/')

    def test_searching_history(self):
        self.assertInSource(re.compile(r'\d+ credits? received.'))
        self.type_in('id_search', '1')
        self.get_search_button().click()
        self.assertInSource(re.compile(r'Searching for “1” returned \d+ credits?.'))

    def test_help_popup(self):
        help_box_heading = self.driver.find_element_by_css_selector('.mtp-disclosure')
        self.assertCssProperty('.mtp-disclosure__contents', 'display', 'none')
        self.assertEqual('false', help_box_heading.get_attribute('aria-expanded'))
        self.click_on_link('Help')
        self.assertCssProperty('.mtp-disclosure__contents', 'display', 'block')
        self.assertEqual('true', help_box_heading.get_attribute('aria-expanded'))
        self.click_on_link('Help')
        self.assertCssProperty('.mtp-disclosure__contents', 'display', 'none')
        self.assertEqual('false', help_box_heading.get_attribute('aria-expanded'))


@silence_logger(name='mtp', level=logging.WARNING)
class AdminPagesTests(CashbookTestCase):
    """
    Tests for Admin pages
    """

    def setUp(self):
        super().setUp()
        self.login('test-prison-1-ua', 'test-prison-1-ua')
        self.click_on_text('Manage users')

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
