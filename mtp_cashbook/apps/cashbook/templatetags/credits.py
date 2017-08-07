import datetime

from django import template
from django.utils import timezone
from django.utils.dateparse import parse_datetime, parse_date
from django.utils.http import urlencode
from django.utils.text import slugify

register = template.Library()


@register.filter
def parse_date_fields(credits):
    """
    MTP API responds with string date/time fields,
    this filter converts them to python objects
    """
    fields = ['received_at', 'credited_at', 'refunded_at', 'logged_at', 'set_manual_at']
    parsers = [parse_datetime, parse_date]

    def convert(credit):
        for field in fields:
            value = credit.get(field, None)
            if not value:
                continue
            for parser in parsers:
                try:
                    parsed_value = parser(value)
                    if not parsed_value:
                        continue
                    if isinstance(parsed_value, datetime.datetime):
                        parsed_value = timezone.localtime(parsed_value)
                    credit[field] = parsed_value
                    break
                except (ValueError, TypeError):
                    pass
        return credit

    return map(convert, credits) if credits else credits


@register.filter
def dayssince(date):
    if isinstance(date, datetime.datetime):
        date = date.date()
    return (datetime.date.today() - date).days


@register.filter
def prefixed_slug(value, prefix='item-'):
    return '%s%s' % (prefix, slugify(value))


@register.filter
def ordering_classes(data, ordering):
    current_ordering = data.get('ordering')
    if current_ordering == ordering:
        return 'mtp-results-ordering mtp-results-ordering--asc'
    if current_ordering == '-%s' % ordering:
        return 'mtp-results-ordering mtp-results-ordering--desc'
    return 'mtp-results-ordering'


@register.inclusion_tag('cashbook/includes/result-ordering-for-screenreader.html')
def describe_ordering_for_screenreader(data, ordering):
    current_ordering = data.get('ordering')
    if current_ordering == ordering:
        ordering = 'ascending'
    elif current_ordering == '-%s' % ordering:
        ordering = 'descending'
    else:
        ordering = None
    return {'ordering': ordering}


@register.filter
def query_string_with_reversed_ordering(data, ordering):
    data = {key: value for key, value in data.items() if value and key != 'page'}
    current_ordering = data.get('ordering')
    if current_ordering == ordering:
        ordering = '-%s' % ordering
    data['ordering'] = ordering
    return urlencode(data, doseq=True)
