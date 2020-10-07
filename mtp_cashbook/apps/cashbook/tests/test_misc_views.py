import copy

from django.urls import reverse, reverse_lazy
from django.test import override_settings
import responses

from cashbook.tests import MTPBaseTestCase, api_url
from mtp_cashbook import READ_ML_BRIEFING_FLAG


class LandingPageTestCase(MTPBaseTestCase):
    def test_requires_login(self):
        response = self.client.get(reverse('home'), follow=True)
        self.assertOnPage(response, 'login')


class MLBriefingTestCase(MTPBaseTestCase):
    confirmation_url = reverse_lazy('ml-briefing-confirmation')
    info_url = reverse_lazy('ml-briefing')

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
        urls = [
            'home',
            'new-credits', 'processed-credits-list', 'search',
            'disbursements:sending_method', 'disbursements:pending_list', 'disbursements:search',
        ]
        for url in urls:
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
