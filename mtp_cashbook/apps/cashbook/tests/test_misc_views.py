import copy

from django.urls import reverse, reverse_lazy
from django.test import override_settings
import responses

from cashbook.tests import MTPBaseTestCase, api_url
from mtp_cashbook import READ_ML_BRIEFING_FLAG, CONFIRM_CREDIT_NOTICE_EMAIL_FLAG


class LandingPageTestCase(MTPBaseTestCase):
    def test_requires_login(self):
        response = self.client.get(reverse('home'), follow=True)
        self.assertOnPage(response, 'login')


class MLBriefingTestCase(MTPBaseTestCase):
    def setUp(self):
        self.unconfirmed_login_data = copy.deepcopy(self._default_login_data)
        flags = list(filter(
            lambda flag: flag != READ_ML_BRIEFING_FLAG,
            self.unconfirmed_login_data['user_data']['flags']
        ))
        self.unconfirmed_login_data['user_data']['flags'] = flags
        super().setUp()

    def test_requires_login(self):
        urls = ['ml-briefing-confirmation', 'ml-briefing']
        for url in urls:
            response = self.client.get(reverse(url), follow=True)
            self.assertOnPage(response, 'login')

    def test_cannot_access_app_without_confirmation_flag(self):
        self.login(login_data=self.unconfirmed_login_data)
        for url in self.main_app_urls:
            response = self.client.get(reverse(url), follow=True)
            self.assertOnPage(response, 'ml-briefing-confirmation')

    def test_cannot_access_confirmation_pages_with_flag(self):
        self.login()
        urls = ['ml-briefing-confirmation', 'ml-briefing']
        for url in urls:
            response = self.client.get(reverse(url), follow=True)
            self.assertOnPage(response, 'home')

    def test_confirming_shows_landing_page(self):
        self.login(login_data=self.unconfirmed_login_data)
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.PUT,
                api_url(
                    f"/users/{self.unconfirmed_login_data['user_data']['username']}/flags/{READ_ML_BRIEFING_FLAG}/"
                ),
                status=200,
            )
            response = self.client.post(
                reverse('ml-briefing-confirmation'),
                data={'read_briefing': 'yes'},
                follow=True,
            )
        self.assertOnPage(response, 'home')

    def test_not_confirming_shows_briefing_info(self):
        self.login(login_data=self.unconfirmed_login_data)
        response = self.client.post(
            reverse('ml-briefing-confirmation'),
            data={'read_briefing': 'no'},
            follow=True,
        )
        self.assertOnPage(response, 'ml-briefing')


class ConfirmCreditNoticeEmailsTestCase(MTPBaseTestCase):
    confirmation_url_name = 'confirm-credit-notice-emails'
    confirmation_url = reverse_lazy(confirmation_url_name)

    def test_requires_login(self):
        response = self.client.get(self.confirmation_url, follow=True)
        self.assertOnPage(response, 'login')

    def test_normal_users_redirected(self):
        self.login()
        response = self.client.get(self.confirmation_url, follow=True)
        self.assertOnPage(response, 'home')

    def test_user_admins_without_flag_redirected(self):
        self.login(login_data=self.get_login_data_for_user_admin())
        response = self.client.get(self.confirmation_url, follow=True)
        self.assertOnPage(response, 'home')

    def test_user_admins_with_flag_redirected_to_confirmation_page(self):
        self.login(login_data=self.get_login_data_for_user_admin(flags=[CONFIRM_CREDIT_NOTICE_EMAIL_FLAG]))
        for url in self.main_app_urls:
            with responses.RequestsMock() as rsps:
                rsps.add(rsps.GET, api_url('/prisoner_credit_notice_email/'), json=[
                    {'prison': 'BXI', 'prison_name': 'HMP Brixton', 'email': 'bxi@mtp.local'},
                ])
                response = self.client.get(reverse(url), follow=True)
            self.assertOnPage(response, self.confirmation_url_name)

    def test_confirmation_page_presents_current_emails(self):
        self.login(login_data=self.get_login_data_for_user_admin(flags=[CONFIRM_CREDIT_NOTICE_EMAIL_FLAG]))
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, api_url('/prisoner_credit_notice_email/'), json=[
                {'prison': 'BXI', 'prison_name': 'HMP Brixton', 'email': 'business-hub@mtp.local'},
                {'prison': 'LEI', 'prison_name': 'HMP Leeds', 'email': 'business-hub@mtp.local'},
            ])
            response = self.client.get(self.confirmation_url)
        response_content = response.content.decode()
        self.assertIn('HMP Brixton: business-hub@mtp.local', response_content)
        self.assertIn('HMP Leeds: business-hub@mtp.local', response_content)
        self.assertIn('Change email', response_content)
        self.assertIn('I’m happy with the current email', response_content)

    def test_confirmation_page_when_no_emails_set_up(self):
        self.login(login_data=self.get_login_data_for_user_admin(flags=[CONFIRM_CREDIT_NOTICE_EMAIL_FLAG]))
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, api_url('/prisoner_credit_notice_email/'), json=[])
            response = self.client.get(self.confirmation_url)
        response_content = response.content.decode()
        self.assertNotIn('Brixton', response_content)  # the user’s prison
        self.assertIn('Set up email address', response_content)
        self.assertIn('I’m happy to not receive credit slips', response_content)

    def assertChoiceRedirects(self, choice, redirected_page):  # noqa: N802
        login_data = self.get_login_data_for_user_admin(flags=[CONFIRM_CREDIT_NOTICE_EMAIL_FLAG])
        username = login_data['user_data']['username']
        self.login(login_data=login_data)
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, api_url('/prisoner_credit_notice_email/'), json=[
                {'prison': 'BXI', 'prison_name': 'HMP Brixton', 'email': 'bxi@mtp.local'},
            ])
            rsps.add(rsps.DELETE, api_url(f'/users/{username}/flags/{CONFIRM_CREDIT_NOTICE_EMAIL_FLAG}/'))
            response = self.client.post(self.confirmation_url, data={'change_email': choice}, follow=True)
        self.assertOnPage(response, redirected_page)

    def test_choosing_to_change_email(self):
        self.assertChoiceRedirects('yes', 'credit-notice-emails')

    def test_choosing_to_leave_email_as_is(self):
        self.assertChoiceRedirects('no', 'home')


class PolicyUpdateTestCase(MTPBaseTestCase):
    def test_requires_login(self):
        response = self.client.get(reverse('home'), follow=True)
        self.assertOnPage(response, 'login')

    @override_settings(BANK_TRANSFERS_ENABLED=True)
    def test_displays_policy_warning_page_before_policy_change(self):
        self.login()
        response = self.client.get(reverse('policy-change'), follow=True)
        self.assertOnPage(response, 'policy-change-warning')

    @override_settings(BANK_TRANSFERS_ENABLED=False)
    def test_displays_policy_update_page_after_policy_change(self):
        self.login()
        response = self.client.get(reverse('policy-change'), follow=True)
        self.assertOnPage(response, 'policy-change-info')
