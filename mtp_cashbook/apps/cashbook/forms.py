import collections
from datetime import timedelta
from math import ceil
from urllib.parse import urlencode

from django import forms
from django.contrib import messages
from django.utils.functional import cached_property
from django.utils.dateformat import format as format_date
from django.utils.safestring import mark_safe
from django.utils.translation import gettext, gettext_lazy, ngettext
from form_error_reporting import GARequestErrorReportingMixin
from mtp_common.api import retrieve_all_pages_for_path
from mtp_common.auth.api_client import get_api_session

from .tasks import credit_selected_credits_to_nomis
from .templatetags.credits import parse_date_fields

MANUALLY_CREDITED_LOG_LEVEL = 21


class ProcessNewCreditsForm(GARequestErrorReportingMixin, forms.Form):
    credits = forms.MultipleChoiceField(choices=(), required=False)

    def __init__(self, request, ordering='-received_at', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.user = request.user
        self.session = get_api_session(request)
        self.ordering = ordering

        self.fields['credits'].choices = self.credit_choices

    def _request_all_credits(self):
        return retrieve_all_pages_for_path(
            self.session, 'credits/', status='credit_pending', resolution='pending',
            ordering=self.ordering
        )

    def clean_credits(self):
        credits = self.cleaned_data.get('credits', [])
        if not credits:
            self.add_error(None, gettext('Only click ‘Credit to NOMIS’ when you’ve selected credits'))
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

        self.session.post('credits/batches/', json={'credits': credit_ids})
        credit_selected_credits_to_nomis(
            user=self.request.user, user_session=self.request.session,
            selected_credit_ids=credit_ids, credits=credits
        )


class ProcessManualCreditsForm(GARequestErrorReportingMixin, forms.Form):
    credit = forms.ChoiceField(choices=(), required=False)

    def __init__(self, request, ordering='-received_at', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.user = request.user
        self.session = get_api_session(request)
        self.ordering = ordering

        self.fields['credit'].choices = self.credit_choices

    def _request_all_credits(self):
        return retrieve_all_pages_for_path(
            self.session, 'credits/', status='credit_pending', resolution='manual',
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
        return [
            (t['id'], t) for t in parse_date_fields(credits)
        ]

    def save(self):
        credit_id = int(self.cleaned_data['credit'])
        self.session.post(
            'credits/actions/credit/',
            json=[{'id': credit_id, 'credited': True}]
        )
        manually_credited = 1
        try:
            manually_credited += int(self.request.GET.get('manually_credited'))
        except (ValueError, TypeError):
            pass
        messages.add_message(
            self.request, MANUALLY_CREDITED_LOG_LEVEL, str(manually_credited)
        )
        return credit_id


class FilterProcessedCreditsListForm(GARequestErrorReportingMixin, forms.Form):
    start = forms.DateField(label=gettext_lazy('From date'),
                            help_text=gettext_lazy('For example, 13/6/2017'),
                            required=False)
    end = forms.DateField(label=gettext_lazy('To date'),
                          help_text=gettext_lazy('For example, 15/6/2017'),
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
        self.session = get_api_session(request)
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
        response = self.session.get(
            'credits/processed/',
            params=dict(offset=offset, limit=self.page_size, **filters)
        ).json()
        return response.get('count', 0), response.get('results', [])

    def get_query_data(self):
        data = collections.OrderedDict()
        for field in self:
            if field.name == 'page':
                continue
            value = self.cleaned_data.get(field.name)
            if value is None:
                value = ''
            data[field.name] = value
        return data

    @cached_property
    def query_string(self):
        return urlencode(self.get_query_data(), doseq=True)


class FilterProcessedCreditsDetailForm(FilterProcessedCreditsListForm):
    names = forms.CharField(
        label=gettext_lazy('Name of prisoner or sender'),
        help_text=gettext_lazy('For example, Bob Phillips'),
        required=False
    )
    prisoner_number = forms.CharField(
        label=gettext_lazy('Prisoner number'),
        help_text=gettext_lazy('For example, A1234AB'),
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
        ('names', 'search'),
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
        credits = retrieve_all_pages_for_path(
            self.session, 'credits/', **dict(self.default_filters, **filters)
        )
        return len(credits), credits


class SearchForm(GARequestErrorReportingMixin, forms.Form):
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
    start = forms.DateField(label=gettext_lazy('From date'),
                            help_text=gettext_lazy('For example, 13/6/2017'),
                            required=False)
    end = forms.DateField(label=gettext_lazy('To date'),
                          help_text=gettext_lazy('For example, 15/6/2017'),
                          required=False)
    search = forms.CharField(label=gettext_lazy('Search'),
                             help_text=gettext_lazy('For example, prisoner name, prisoner number or sender name'),
                             required=False)
    page = forms.IntegerField(required=False, widget=forms.HiddenInput)

    page_size = 20

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ''
        self.request = request
        self.user = request.user
        self.session = get_api_session(request)
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

    def clean_ordering(self):
        return self.cleaned_data.get('ordering') or self.fields['ordering'].initial

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

        renames = (
            ('start', 'received_at__gte'),
            ('end', 'received_at__lt'),
        )
        for field_name, api_name in renames:
            if field_name in filters:
                filters[api_name] = filters[field_name]
                del filters[field_name]

        page = self.cleaned_data.get('page') or 1
        offset = (page - 1) * self.page_size
        response = self.session.get(
            'credits/',
            params=dict(offset=offset, limit=self.page_size, resolution='credited', **filters)
        ).json()
        count = response.get('count', 0)
        self.pagination = {
            'page': page,
            'count': count,
            'full_count': count,
            'page_count': int(ceil(count / self.page_size)),
        }
        results = response.get('results', [])
        if page == 1:
            new_credits = retrieve_all_pages_for_path(
                self.session, 'credits/', status='credit_pending', **filters
            )
            self.pagination['full_count'] += len(new_credits)
            results = new_credits + results
        return parse_date_fields(results)

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
        if self.pagination['full_count']:
            credit_description = ngettext(
                '%(count)s credit',
                '%(count)s credits',
                self.pagination['full_count'],
            ) % {'count': '<strong>{:,}</strong>'.format(self.pagination['full_count'])}
        else:
            return gettext('No credits found')

        search_description, date_range_description = self._get_filter_description()
        if date_range_description:
            description = gettext('Showing %(credits)s received %(date_range)s') % {
                'date_range': date_range_description,
                'credits': credit_description,
            }
        elif search_description:
            description = gettext('Showing %(credits)s received') % {
                'credits': credit_description,
            }
        else:
            description = gettext('Showing all %(credits)s received') % {
                'credits': credit_description,
            }
        return mark_safe(description)

    def get_query_data(self):
        data = collections.OrderedDict()
        for field in self:
            if field.name == 'page':
                continue
            value = self.cleaned_data.get(field.name)
            if value is None:
                value = ''
            data[field.name] = value
        return data

    @cached_property
    def query_string(self):
        return urlencode(self.get_query_data(), doseq=True)
