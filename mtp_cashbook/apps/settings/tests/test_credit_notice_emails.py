import copy

from django.urls import reverse
import responses

from cashbook.tests import MTPBaseTestCase, api_url


class SettingsPageTestCase(MTPBaseTestCase):
    def test_non_admins_see_no_settings(self):
        self.login()
        with responses.RequestsMock():
            response = self.client.get(reverse('settings'))
        self.assertNotContains(response, 'Email address for credit slips')
        self.assertNotContains(response, 'Not set up in your prison')

    def get_login_data_for_user_admin(self):
        login_data_for_user_admin = copy.deepcopy(self._default_login_data)
        login_data_for_user_admin['user_data']['user_admin'] = True
        return login_data_for_user_admin

    def test_show_unconfigured_settings(self):
        self.login(login_data=self.get_login_data_for_user_admin())
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, api_url('/prisoner_credit_notice_email/'), json=[])
            response = self.client.get(reverse('settings'))
        self.assertContains(response, 'Email address for credit slips')
        self.assertContains(response, 'Not set up in your prison')

    def test_show_typical_settings(self):
        self.login(login_data=self.get_login_data_for_user_admin())
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, api_url('/prisoner_credit_notice_email/'), json=[
                {'prison': 'BXI', 'prison_name': 'HMP Brixton', 'email': 'business-hub@mtp.local'},
            ])
            response = self.client.get(reverse('settings'))
        self.assertContains(response, 'Email address for credit slips')
        self.assertContains(response, 'HMP Brixton: business-hub@mtp.local')

    def test_show_settings_for_multiple_prisons(self):
        self.login(login_data=self.get_login_data_for_user_admin())
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, api_url('/prisoner_credit_notice_email/'), json=[
                {'prison': 'BXI', 'prison_name': 'HMP Brixton', 'email': 'business-hub@mtp.local'},
                {'prison': 'LEI', 'prison_name': 'HMP Leeds', 'email': 'business-hub@mtp.local'},
            ])
            response = self.client.get(reverse('settings'))
        self.assertContains(response, 'HMP Brixton: business-hub@mtp.local')
        self.assertContains(response, 'HMP Leeds: business-hub@mtp.local')
