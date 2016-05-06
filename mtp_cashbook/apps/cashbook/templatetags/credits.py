from collections import OrderedDict
import datetime
from itertools import groupby
from urllib import parse as urlparse

from django import template
from django.utils import timezone
from django.utils.dateparse import parse_datetime, parse_date

register = template.Library()


@register.filter
def parse_date_fields(credits):
    """
    MTP API responds with string date/time fields,
    this filter converts them to python objects
    """
    fields = ['received_at', 'credited_at', 'refunded_at']
    parsers = [parse_datetime, parse_date]

    def convert(credit):
        for field in fields:
            value = credit[field]
            if not value:
                continue
            for parser in parsers:
                try:
                    value = parser(value)
                    if isinstance(value, datetime.datetime):
                        value = timezone.localtime(value)
                    credit[field] = value
                    break
                except (ValueError, TypeError):
                    pass
        return credit

    return map(convert, credits)


@register.filter
def regroup_credits(credits):
    """
    Groups credits into days (by received_at) and refunded status
    """
    def get_status_key(t):
        if not t['resolution'] == 'credited':
            return 'uncredited'
        if t['resolution'] == 'refunded':
            return 'refunded'
        return 'credited'

    def get_status_order(t):
        if not t['resolution'] == 'credited':
            return 0
        if not t['resolution'] == 'refunded':
            return 1
        return 2

    def get_order_key(t):
        return t['prisoner_number']

    grouped_credits = OrderedDict()
    groups = groupby(credits, key=lambda t: t['received_at'].date() if t['received_at'] else None)
    for date, group in groups:
        # NB: listing out inner generators so that results can be iterated multiple times
        grouped = groupby(sorted(group, key=get_status_order), key=get_status_key)
        grouped = ((status_key, list(sorted(items, key=get_order_key))) for (status_key, items) in grouped)
        grouped_credits[date] = grouped
    return grouped_credits.items()


@register.filter
def sum_credits(credits):
    """
    Returns the total sum of payment amounts (irrespective of status)
    """
    return sum(map(lambda t: t['amount'] or 0, credits))


@register.simple_tag
def url_with_query_param(request, param_name, value):
    """
    Sets or replaces a GET query parameter or the current URL with a new value
    """

    # adapted from Django REST Framework:
    def replace_query_param(url, key, val):
        """
        Given a URL and a key/val pair, set or replace an item in the query
        parameters of the URL, and return the new URL.
        """
        (scheme, netloc, path, query, fragment) = urlparse.urlsplit(url)
        query_dict = urlparse.parse_qs(query, keep_blank_values=True)
        query_dict[key] = [val]
        query = urlparse.urlencode(sorted(list(query_dict.items())), doseq=True)
        return urlparse.urlunsplit((scheme, netloc, path, query, fragment))

    url = request.build_absolute_uri()
    return replace_query_param(url, param_name, value)
