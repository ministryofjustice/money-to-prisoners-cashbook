from collections import OrderedDict
from itertools import groupby
from urllib import parse as urlparse

from django import template
from django.utils.dateparse import parse_datetime, parse_date

register = template.Library()


@register.filter
def parse_date_fields(transactions):
    """
    MTP API responds with string date/time fields,
    this filter converts them to python objects
    """
    fields = ['received_at', 'credited_at', 'refunded_at']
    parsers = [parse_datetime, parse_date]

    def convert(transaction):
        for field in fields:
            value = transaction[field]
            if not value:
                continue
            for parser in parsers:
                try:
                    transaction[field] = parser(value)
                    break
                except (ValueError, TypeError):
                    pass
        return transaction

    return map(convert, transactions)


@register.filter
def regroup_transactions(transactions):
    """
    Groups transactions into days (by received_at) and refunded status
    """
    def get_status_key(t):
        if not t['credited']:
            return 'uncredited'
        if t['refunded']:
            return 'refunded'
        return 'credited'

    def get_status_order(t):
        if not t['credited']:
            return 0
        if not t['refunded']:
            return 1
        return 2

    def get_order_key(t):
        return t['prisoner_number']

    grouped_transactions = OrderedDict()
    groups = groupby(transactions, key=lambda t: t['received_at'].date() if t['received_at'] else None)
    for date, group in groups:
        # NB: listing out inner generators so that results can be iterated multiple times
        grouped = groupby(sorted(group, key=get_status_order), key=get_status_key)
        grouped = ((status_key, list(sorted(items, key=get_order_key))) for (status_key, items) in grouped)
        grouped_transactions[date] = grouped
    return grouped_transactions.items()


@register.filter
def sum_transactions(transactions):
    """
    Returns the total sum of payment amounts (irrespective of status)
    """
    return sum(map(lambda t: t['amount'] or 0, transactions))


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
