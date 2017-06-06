import collections
from datetime import timedelta
from functools import reduce
from itertools import groupby
import logging
from math import ceil
from urllib.parse import urlencode

from django import forms
from django.conf import settings
from django.utils.dateparse import parse_datetime
from django.utils.functional import cached_property
from django.utils.dateformat import format as format_date
from django.utils.text import capfirst
from django.utils.translation import gettext, gettext_lazy, ngettext
from form_error_reporting import GARequestErrorReportingMixin
from mtp_common.api import retrieve_all_pages
from mtp_common.auth.api_client import get_connection

from .tasks import credit_selected_credits_to_nomis
from .templatetags.credits import parse_date_fields

logger = logging.getLogger('mtp')

COMPLETED_INDEX = 21


class ProcessCreditBatchForm(GARequestErrorReportingMixin, forms.Form):
    credits = forms.MultipleChoiceField(choices=(), required=False)

    def __init__(self, request, *args, **kwargs):
        super(ProcessCreditBatchForm, self).__init__(*args, **kwargs)
        self.request = request
        self.user = request.user
        self.client = get_connection(request)

        self.fields['credits'].choices = self.credit_choices

    def _request_locked_credits(self):
        return retrieve_all_pages(self.client.credits.get,
                                  status='locked', user=self.user.pk)

    def _take_credits(self):
        self.client.credits.actions.lock.post()

    def clean_credits(self):
        """
        If discard button clicked => ignore any credits that might
        have been ticked.
        """
        credits = self.cleaned_data.get('credits', [])
        discard = self.data.get('discard') == '1'
        if not credits and not discard:
            self.add_error(None, gettext('Only click ‘Done’ when you’ve selected credits'))
        if discard:
            credits = []
        return credits

    @cached_property
    def credit_choices(self):
        """
        Gets the credits currently locked by the user if they exist
        or locks some and returns them if not.
        """
        credits = self._request_locked_credits()
        if not self.is_bound and len(credits) == 0:
            self._take_credits()
            credits = self._request_locked_credits()

        return [
            (t['id'], t) for t in parse_date_fields(credits)
        ]

    def save(self):
        all_ids = {str(t[0]) for t in self.credit_choices}
        to_credit = set(self.cleaned_data['credits'])
        to_discard = all_ids - to_credit

        # The two calls to the api might return a status code != 2xx
        # but we are allowing them to raise an exception here.
        # This shouldn't really happen but if it does often enough,
        # we might want to add some exception handling.

        # credit
        if to_credit:
            self.client.credits.patch(
                [{'id': t_id, 'credited': True} for t_id in to_credit]
            )

        # discard
        if to_discard:
            self.client.credits.actions.unlock.post({
                'credit_ids': list(to_discard)
            })

        return (to_credit, to_discard)


class DiscardLockedCreditsForm(GARequestErrorReportingMixin, forms.Form):
    credits = forms.MultipleChoiceField(choices=(), required=False)

    def __init__(self, request, *args, **kwargs):
        super(DiscardLockedCreditsForm, self).__init__(*args, **kwargs)
        self.request = request
        self.user = request.user
        self.client = get_connection(request)

        self.fields['credits'].choices = self.grouped_credit_choices

    def _request_locked_credits(self):
        return retrieve_all_pages(self.client.credits.locked.get)

    def clean_credits(self):
        credits = self.cleaned_data.get('credits')
        if not credits:
            self.add_error(
                None,
                gettext('Only click ‘Done’ when you’ve selected the row of credits you want to release')
            )
        return credits

    @cached_property
    def credit_choices(self):
        """
        Gets the credits currently locked by all users for prison
        """
        credits = self._request_locked_credits()

        return [
            (t['id'], t) for t in credits
        ]

    @cached_property
    def grouped_credit_choices(self):
        """
        Gets credits grouped by prison clerk who currently has them locked
        for current prison
        """
        credits = self._request_locked_credits()

        # group by locking prison clerk (needs sort first)
        credits = sorted(credits, key=lambda t: '%s%d' % (t['owner_name'], t['owner']))
        grouped_credits = []
        for owner, group in groupby(credits, key=lambda t: t['owner']):
            group = list(group)

            locked_ids = ' '.join(sorted(str(t['id']) for t in group))
            grouped_credits.append((locked_ids, {
                'owner': group[0]['owner'],
                'owner_name': group[0]['owner_name'],
                'owner_prison': group[0]['prison'],
                'locked_count': len(group),
                'locked_amount': sum((t['amount'] for t in group)),
                'locked_at_earliest': parse_datetime(min((t['locked_at'] for t in group))),
            }))
        return grouped_credits

    def save(self):
        credit_ids = map(str.split, self.cleaned_data['credits'])
        credit_ids = reduce(list.__add__, credit_ids, [])
        to_discard = set(credit_ids)

        # discard
        if to_discard:
            self.client.credits.actions.unlock.post({
                'credit_ids': list(to_discard)
            })

        return to_discard


class FilterCreditHistoryForm(GARequestErrorReportingMixin, forms.Form):
    start = forms.DateField(label=gettext_lazy('From'), required=False)
    end = forms.DateField(label=gettext_lazy('To'), required=False)
    search = forms.CharField(label=gettext_lazy('Prisoner name, prisoner number or sender name'), required=False)
    page = forms.IntegerField(required=False, widget=forms.HiddenInput)

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ''
        self.request = request
        self.user = request.user
        self.client = get_connection(request)
        self.pagination = {
            'page': 1,
            'count': 0,
            'page_count': 0,
        }

    def clean(self):
        start = self.cleaned_data.get('start')
        end = self.cleaned_data.get('end')
        if start and end and start >= end:
            self.add_error('end', gettext('The end date must be after the start date'))
        return super().clean()

    def clean_end(self):
        end = self.cleaned_data.get('end')
        if end is not None:
            return end + timedelta(days=1)

    @property
    def has_filters(self):
        if not hasattr(self, 'cleaned_data'):
            return False
        return any(self.cleaned_data.get(key) for key in ['start', 'end', 'search'])

    @cached_property
    def credit_choices(self):
        page_size = settings.REQUEST_PAGE_DAYS
        filters = {
            'ordering': '-received_at',
            'page_by_date_field': 'received_at',
            'page_size': page_size,
        }

        fields = set(self.fields.keys())
        if self.is_valid():
            # valid form
            for field in fields:
                if field in self.cleaned_data:
                    filters[field] = self.cleaned_data[field]
        elif not self.is_bound:
            # no form submission
            for field in fields:
                if field in self.initial:
                    filters[field] = self.initial[field]
        else:
            # invalid form
            self.pagination = {
                'page': 1,
                'count': 0,
                'page_count': 0,
            }
            return []

        renames = (
            ('start', 'received_at__gte'),
            ('end', 'received_at__lt'),
        )
        for field_name, api_name in renames:
            if field_name in filters:
                filters[api_name] = filters[field_name]
                del filters[field_name]

        response = self.client.credits.get(**filters)
        self.pagination = {
            'page': response.get('page', 1),
            'count': response.get('count', 0),
            'page_count': response.get('page_count', 0),
        }
        return response.get('results', [])

    def _get_filter_description(self):
        if self.cleaned_data:
            search_description = self.cleaned_data.get('search')

            def get_date(date_key):
                date = self.cleaned_data.get(date_key)
                if date:
                    return format_date(date, 'd/m/Y')

            date_range = {
                'start': get_date('start'),
                'end': get_date('end'),
            }
            if date_range['start'] and date_range['end']:
                if date_range['start'] == date_range['end']:
                    date_range_description = gettext('on %(start)s') % date_range
                else:
                    date_range_description = gettext('between %(start)s and %(end)s') % date_range
            elif date_range['start']:
                date_range_description = gettext('since %(start)s') % date_range
            elif date_range['end']:
                date_range_description = gettext('up to %(end)s') % date_range
            else:
                date_range_description = None
        else:
            search_description = None
            date_range_description = None
        return search_description, date_range_description

    def get_search_description(self):
        if self.pagination['count']:
            credit_description = ngettext(
                '%(count)d credit',
                '%(count)d credits',
                self.pagination['count'],
            ) % self.pagination
        else:
            credit_description = gettext('no credits')

        search_description, date_range_description = self._get_filter_description()
        if search_description and date_range_description:
            description = gettext('%(credits)s received %(date_range)s when searching for “%(search)s”') % {
                'search': search_description,
                'date_range': date_range_description,
                'credits': credit_description,
            }
        elif search_description:
            description = gettext('Searching for “%(search)s” returned %(credits)s') % {
                'search': search_description,
                'credits': credit_description,
            }
        elif date_range_description:
            description = gettext('%(credits)s received %(date_range)s') % {
                'date_range': date_range_description,
                'credits': credit_description,
            }
        else:
            description = gettext('%(credits)s received') % {
                'credits': credit_description,
            }
        return capfirst(description)

    def get_query_data(self):
        data = collections.OrderedDict()
        for field in self:
            if field.name == 'page':
                continue
            value = self.cleaned_data.get(field.name)
            if value in [None, '', []]:
                continue
            data[field.name] = value
        return data

    @cached_property
    def query_string(self):
        return urlencode(self.get_query_data(), doseq=True)


class ProcessNewCreditsForm(GARequestErrorReportingMixin, forms.Form):
    credits = forms.MultipleChoiceField(choices=(), required=False)

    def __init__(self, request, ordering='-received_at', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.user = request.user
        self.client = get_connection(request)
        self.ordering = ordering

        self.fields['credits'].choices = self.credit_choices

    def _request_all_credits(self):
        return retrieve_all_pages(
            self.client.credits.get, status='credit_pending', resolution='pending',
            ordering=self.ordering
        )

    def clean_credits(self):
        credits = self.cleaned_data.get('credits', [])
        if not credits:
            self.add_error(None, gettext('Only click ‘Done’ when you’ve selected credits'))
        return credits

    @cached_property
    def credit_choices(self):
        """
        Gets the credits currently available the user.
        """
        credits = self._request_all_credits()
        return [
            (t['id'], t) for t in parse_date_fields(credits)
        ]

    def save(self):
        credit_ids = [int(c_id) for c_id in set(self.cleaned_data['credits'])]
        credits = dict(self.credit_choices)

        self.client.credits.batches.post({'credits': credit_ids})
        credit_selected_credits_to_nomis(
            self.request.user, self.request.session, credit_ids, credits
        )


class ProcessManualCreditsForm(GARequestErrorReportingMixin, forms.Form):
    credit = forms.ChoiceField(choices=(), required=False)

    def __init__(self, request, ordering='-received_at', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.user = request.user
        self.client = get_connection(request)
        self.ordering = ordering

        self.fields['credit'].choices = self.credit_choices

    def _request_all_credits(self):
        return retrieve_all_pages(
            self.client.credits.get, status='credit_pending', resolution='manual',
            ordering=self.ordering
        )

    def clean_credit(self):
        prefix = 'submit_manual_'
        if self.request.method == 'POST':
            for key in self.request.POST:
                if key.startswith(prefix):
                    credit_id = int(key[len(prefix):])
                    if not self.credit_choices or credit_id not in next(zip(*self.credit_choices)):
                        raise forms.ValidationError(
                            gettext_lazy('That credit cannot be manually credited'), code='invalid'
                        )
                    return credit_id

    @cached_property
    def credit_choices(self):
        """
        Gets the credits currently available the user.
        """
        credits = self._request_all_credits()
        id_credits = []
        for credit in parse_date_fields(credits):
            id_credits.append((credit['id'], credit))
        return id_credits

    def save(self):
        credit_id = int(self.cleaned_data['credit'])
        self.client.credits.actions.credit.post([
            {'id': credit_id, 'credited': True}
        ])
        return credit_id


class FilterProcessedCreditsListForm(GARequestErrorReportingMixin, forms.Form):
    start = forms.DateField(label=gettext_lazy('From date'),
                            help_text=gettext_lazy('e.g. 1/6/2016'),
                            required=False)
    end = forms.DateField(label=gettext_lazy('to date'),
                          help_text=gettext_lazy('e.g. 5/6/2016'),
                          required=False)
    page = forms.IntegerField(required=False, widget=forms.HiddenInput)

    page_size = 20
    renames = (
        ('start', 'logged_at__gte'),
        ('end', 'logged_at__lt'),
    )

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ''
        self.request = request
        self.user = request.user
        self.client = get_connection(request)
        self.pagination = {
            'page': 1,
            'count': 0,
            'page_count': 0,
        }

    def clean(self):
        start = self.cleaned_data.get('start')
        end = self.cleaned_data.get('end')
        if start and end and start >= end:
            self.add_error('end', gettext('The end date must be after the start date'))
        return super().clean()

    def clean_end(self):
        end = self.cleaned_data.get('end')
        if end is not None:
            return end + timedelta(days=1)

    @cached_property
    def credit_choices(self):
        filters = {}
        fields = set(self.fields.keys())
        if self.is_valid():
            # valid form
            for field in fields:
                if field in self.cleaned_data:
                    filters[field] = self.cleaned_data[field]
        elif not self.is_bound:
            # no form submission
            for field in fields:
                if field in self.initial:
                    filters[field] = self.initial[field]

        for field_name, api_name in self.renames:
            if field_name in filters:
                filters[api_name] = filters[field_name]
                del filters[field_name]

        page = self.cleaned_data.get('page') or 1
        offset = (page - 1) * self.page_size
        count, results = self.retrieve_credits(offset, self.page_size, **filters)
        self.pagination = {
            'page': page,
            'count': count,
            'page_count': int(ceil(count / self.page_size)),
        }
        return parse_date_fields(results)

    def retrieve_credits(self, offset, limit, **filters):
        response = self.client.credits.processed.get(offset=offset, limit=self.page_size, **filters)
        return response.get('count', 0), response.get('results', [])

    def get_query_data(self):
        data = collections.OrderedDict()
        for field in self:
            if field.name == 'page':
                continue
            value = self.cleaned_data.get(field.name)
            if value in [None, '', []]:
                continue
            data[field.name] = value
        return data

    @cached_property
    def query_string(self):
        return urlencode(self.get_query_data(), doseq=True)


class FilterProcessedCreditsDetailForm(FilterProcessedCreditsListForm):
    search = forms.CharField(
        label=gettext_lazy('Name of prisoner or sender'),
        help_text=gettext_lazy('e.g. Bob Phillips'),
        required=False
    )
    prisoner_number = forms.CharField(
        label=gettext_lazy('Prisoner number'),
        help_text=gettext_lazy('e.g. A1234AB'),
        required=False
    )
    ordering = forms.ChoiceField(
        label=gettext_lazy('Order by'), required=False,
        initial='-received_at',
        choices=[
            ('received_at', gettext_lazy('Received date (oldest to newest)')),
            ('-received_at', gettext_lazy('Received date (newest to oldest)')),
            ('amount', gettext_lazy('Amount sent (low to high)')),
            ('-amount', gettext_lazy('Amount sent (high to low)')),
            ('prisoner_number', gettext_lazy('Prisoner number (A to Z)')),
            ('-prisoner_number', gettext_lazy('Prisoner number (Z to A)')),
        ]
    )
    renames = (
        ('start', 'received_at__gte'),
        ('end', 'received_at__lt'),
    )

    def __init__(self, request, date, user_id, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        self.batch_date = date
        self.default_filters = {
            'log__action': 'credited',
            'logged_at__gte': self.batch_date,
            'logged_at__lt': self.batch_date + timedelta(days=1),
            'user': user_id
        }

    def clean_ordering(self):
        return self.cleaned_data['ordering'] or self.fields['ordering'].initial

    def retrieve_credits(self, offset, limit, **filters):
        response = self.client.credits.get(
            offset=offset, limit=self.page_size, **dict(self.default_filters, **filters)
        )
        return response.get('count', 0), response.get('results', [])
