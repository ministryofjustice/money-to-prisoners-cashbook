import datetime
from django.test import SimpleTestCase, override_settings
from django.urls import reverse
from django.utils.html import strip_tags
import responses

from cashbook.tests import MTPBaseTestCase, api_url
from disbursements.forms import SearchForm


@override_settings(DISBURSEMENT_PRISONS=['BXI'])
class DisbursementSearchViewTextCase(MTPBaseTestCase):
    user = {'username': 'abc123', 'first_name': 'A', 'last_name': 'User'}

    @property
    def url(self):
        return reverse('disbursements:search')

    def test_no_disbursements_response(self):
        self.login()
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, api_url('/disbursements/?resolution=pending&limit=1',),
                     json={'count': 0, 'results': []}, match_querystring=True)
            rsps.add(rsps.GET, api_url('/disbursements/',),
                     json={'count': 0, 'results': []})
            response = self.client.get(self.url)
        self.assertContains(response, 'No disbursements found')
        form = response.context_data['form']
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['page'], 1)
        self.assertEqual(form.cleaned_data['ordering'], '-created')
        self.assertEqual(form.cleaned_data['date_filter'], 'confirmed')
        content = response.content.decode()
        self.assertNotIn('This service is currently unavailable', content)

    def test_disbursements_listed(self):
        self.login()
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, api_url('/disbursements/?resolution=pending&limit=1',),
                     json={'count': 1, 'results': []}, match_querystring=True)
            rsps.add(rsps.GET, api_url('/disbursements/',),
                     json={'count': 1, 'results': [{
                         'id': 100, 'amount': 1250, 'invoice_number': 'PMD1000100',
                         'method': 'cheque', 'resolution': 'sent', 'nomis_transaction_id': '123-1',
                         'prisoner_name': 'JOHN HALLS', 'prisoner_number': 'A1409AE',
                         'recipient_is_company_name': False,
                         'recipient_first_name': 'FN', 'recipient_last_name': 'SN', 'recipient_email': '',
                         'address_line1': '102 Petty France', 'address_line2': '',
                         'city': 'London', 'postcode': 'SW1H 9AJ', 'country': 'UK',
                         'sort_code': '', 'account_number': '', 'roll_number': '',
                         'log_set': [{'action': 'created', 'created': '2018-01-10T08:00:00Z',
                                      'user': self.user},
                                     {'action': 'confirmed', 'created': '2018-01-10T09:00:00Z',
                                      'user': self.user},
                                     {'action': 'sent', 'created': '2018-01-10T10:00:00Z',
                                      'user': self.user}],
                     }]})
            response = self.client.get(self.url)
        content = response.content.decode()
        self.assertNotIn('This service is currently unavailable', content)
        self.assertIn('Cheque', content)
        self.assertNotIn('Bank transfer', content)
        self.assertIn('Confirmed 10/01/2018', content)
        self.assertIn('Sent to SSCL', content)
        self.assertIn('PMD1000100', content)
        self.assertIn('£12.50', content)
        self.assertIn('123-1', content)
        self.assertIn('JOHN HALLS', content)
        self.assertIn('A1409AE', content)
        self.assertIn('FN SN', content)
        self.assertIn('102 Petty France', content)
        self.assertIn('London', content)
        self.assertIn('SW1H 9AJ', content)
        self.assertIn('Page 1 of 1', content)

    def test_disbursements_search(self):
        self.login()
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, api_url('/disbursements/?offset=10&limit=10&ordering=-created&resolution=confirmed',),
                     match_querystring=True,
                     json={'count': 11, 'results': [{
                         'id': 99, 'amount': 25010, 'invoice_number': '1000099',
                         'method': 'bank_transfer', 'resolution': 'confirmed', 'nomis_transaction_id': None,
                         'prisoner_name': 'JOHN HALLS', 'prisoner_number': 'A1409AE',
                         'recipient_is_company_name': False,
                         'recipient_first_name': 'FN', 'recipient_last_name': 'SN', 'recipient_email': 'email@local',
                         'address_line1': '13 Place Vendôme', 'address_line2': '',
                         'city': 'Paris', 'postcode': '75001', 'country': 'France',
                         'sort_code': '000000', 'account_number': '1234567890', 'roll_number': '',
                         'log_set': [{'action': 'created', 'created': '2018-01-10T08:00:00Z',
                                      'user': self.user},
                                     {'action': 'confirmed', 'created': '2018-01-10T09:00:00Z',
                                      'user': self.user}],
                     }]})
            response = self.client.get(self.url + '?page=2&resolution=confirmed')
        form = response.context_data['form']
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['page'], 2)
        self.assertEqual(form.cleaned_data['resolution'], 'confirmed')
        content = response.content.decode()
        self.assertNotIn('This service is currently unavailable', content)
        self.assertNotIn('Cheque', content)
        self.assertIn('Account 1234567890', content)
        self.assertIn('Confirmed 10/01/2018', content)
        self.assertNotIn('Sent by SSCL', content)
        self.assertNotIn('1000099', content)
        self.assertIn('£250.10', content)
        self.assertIn('France', content)
        self.assertIn('00-00-00', content)
        self.assertIn('1234567890', content)
        self.assertIn('email@local', content)
        self.assertIn('Page 2 of 2', content)


class DisbursementSearchFormTextCase(SimpleTestCase):
    def test_blank_form_valid(self):
        form = SearchForm(request=None, data={})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['page'], 1)
        description = form.search_description
        self.assertFalse(description['has_filters'])
        self.assertIn('Showing all disbursements', description['description'])

    def test_invalid_options(self):
        form = SearchForm(request=None, data={
            'page': 0,
            'ordering': 'date',
            'method': 'cash',
            'resolution': 'preconfirmed',
        })
        self.assertFalse(form.is_valid())
        errors = form.errors.as_data()
        self.assertIn('page', errors)
        self.assertIn('ordering', errors)
        self.assertIn('method', errors)
        self.assertIn('resolution', errors)

    def test_date_options(self):
        form = SearchForm(request=None, data={
            'date_filter': 'created',
            'date__gte': '10/1/18',
            'date__lt': '11/01/2018',
        })
        self.assertTrue(form.is_valid())
        query_params = form.get_api_request_params()
        query_params.pop('resolution', None)
        self.assertDictEqual(query_params, {
            'ordering': '-created',
            'log__action': 'created',
            'logged_at__gte': datetime.date(2018, 1, 10),
            'logged_at__lt': datetime.date(2018, 1, 12),
        })
        description = form.search_description
        self.assertTrue(description['has_filters'])
        self.assertIn('date entered between 10 Jan 2018 and 11 Jan 2018', strip_tags(description['description']))

        form = SearchForm(request=None, data={
            'ordering': '-amount',
            'date_filter': 'confirmed',
            'date__lt': '2018-01-10',
        })
        self.assertTrue(form.is_valid())
        query_params = form.get_api_request_params()
        query_params.pop('resolution', None)
        self.assertDictEqual(query_params, {
            'ordering': '-amount',
            'log__action': 'confirmed',
            'logged_at__lt': datetime.date(2018, 1, 11),
        })
        description = form.search_description
        self.assertTrue(description['has_filters'])
        self.assertIn('date confirmed before 10 Jan 2018', strip_tags(description['description']))
