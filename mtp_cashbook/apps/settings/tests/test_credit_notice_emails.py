import copy

from django.urls import reverse
from mtp_common.test_utils import silence_logger
import responses

from cashbook.tests import MTPBaseTestCase, api_url


class CreditNoticeEmailsBaseTestCase(MTPBaseTestCase):
    def get_login_data_for_user_admin(self, prisons=None):
        login_data_for_user_admin = copy.deepcopy(self._default_login_data)
        login_data_for_user_admin['user_data']['user_admin'] = True
        if prisons:
            login_data_for_user_admin['user_data']['prisons'] = prisons
        return login_data_for_user_admin


class SettingsPageTestCase(CreditNoticeEmailsBaseTestCase):
    def test_non_admins_see_no_settings(self):
        self.login()
        with responses.RequestsMock():
            response = self.client.get(reverse('settings'))
        self.assertNotContains(response, 'Email address for credit slips')
        self.assertNotContains(response, 'Not set up in your prison')

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

    def test_show_note_when_not_set_up(self):
        self.login(login_data=self.get_login_data_for_user_admin())
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, api_url('/prisoner_credit_notice_email/'), json=[])
            response = self.client.get(reverse('settings'))
        self.assertContains(response, 'Set up email')


class EditPageTestCase(CreditNoticeEmailsBaseTestCase):
    def test_non_admins_see_no_settings(self):
        self.login()
        with responses.RequestsMock(), silence_logger('django.request'):
            response = self.client.get(reverse('credit-notice-emails'))
        self.assertEqual(response.status_code, 404)

    def test_initial_value_from_current_settings(self):
        self.login(login_data=self.get_login_data_for_user_admin())
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, api_url('/prisoner_credit_notice_email/'), json=[
                {'prison': 'BXI', 'prison_name': 'HMP Brixton', 'email': 'bxi@mtp.local'},
                {'prison': 'LEI', 'prison_name': 'HMP Leeds', 'email': 'lei@mtp.local'},
            ])
            response = self.client.get(reverse('credit-notice-emails'))
        self.assertContains(response, 'New email address')
        self.assertEqual(response.context_data['form']['email'].initial, 'bxi@mtp.local')

    def test_saves_email_for_user_prisons(self):
        self.login(login_data=self.get_login_data_for_user_admin([
            {'nomis_id': 'BXI', 'name': 'HMP Brixton', 'pre_approval_required': False},
            {'nomis_id': 'LEI', 'name': 'HMP Leeds', 'pre_approval_required': False},
        ]))
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, api_url('/prisoner_credit_notice_email/'), json=[
                {'prison': 'BXI', 'prison_name': 'HMP Brixton', 'email': 'bxi@mtp.local'},
                {'prison': 'LEI', 'prison_name': 'HMP Leeds', 'email': 'lei@mtp.local'},
            ])
            rsps.add(rsps.PATCH, api_url('/prisoner_credit_notice_email/BXI/'), json={'email': 'new@mtp.local'})
            rsps.add(rsps.PATCH, api_url('/prisoner_credit_notice_email/LEI/'), json={'email': 'new@mtp.local'})
            response = self.client.post(reverse('credit-notice-emails'), data={'email': 'new@mtp.local'}, follow=True)
        self.assertOnPage(response, 'settings')
        self.assertContains(response, 'Email address for credit slips changed')

    def test_failing_to_saves_email_shows_error(self):
        self.login(login_data=self.get_login_data_for_user_admin())
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.GET, api_url('/prisoner_credit_notice_email/'),
                json=[
                    {'prison': 'BXI', 'prison_name': 'HMP Brixton', 'email': 'bxi@mtp.local'},
                ],
            )
            # pretend the model was deleted at the same moment
            rsps.add(
                rsps.PATCH, api_url('/prisoner_credit_notice_email/BXI/'),
                status=404,
                json={'detail': 'Not found.'},
            )
            with silence_logger():
                response = self.client.post(reverse('credit-notice-emails'), data={'email': 'new@mtp.local'})
        self.assertOnPage(response, 'credit-notice-emails')
        self.assertContains(response, 'Could not save email for HMP Brixton')
        self.assertNotContains(response, 'Not found')
