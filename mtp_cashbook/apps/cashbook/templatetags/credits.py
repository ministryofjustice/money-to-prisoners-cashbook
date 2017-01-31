from collections import OrderedDict
import datetime
from itertools import groupby
from urllib import parse as urlparse

from django import template
from django.utils import timezone
from django.utils.dateparse import parse_datetime, parse_date
from django.utils.translation import gettext_lazy as _

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
            value = credit.get(field, None)
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

    return map(convert, credits) if credits else credits


@register.filter
def dayssince(date):
    if isinstance(date, datetime.datetime):
        date = date.date
    return (datetime.date.today() - date).days


@register.filter
def regroup_credits(credits):
    """
    Groups credits into days (by received_at) and refunded status
    """
    def get_status_key(c):
        if c['resolution'] == 'refunded':
            return 'refunded'
        if c['resolution'] == 'credited':
            return 'credited'
        if c['anonymous']:
            return 'anonymous'
        return 'uncredited'

    def get_status_order(c):
        if c['resolution'] == 'credited':
            return 3
        if c['resolution'] == 'refunded':
            return 2
        if c['anonymous']:
            return 1
        return 0

    grouped_credits = OrderedDict()
    groups = groupby(credits, key=lambda c: c['received_at'].date() if c['received_at'] else None)
    for date, group in groups:
        # NB: listing out inner generators so that results can be iterated multiple times
        grouped = groupby(sorted(group, key=get_status_order), key=get_status_key)
        grouped = (
            (status_key, list(sorted(items, key=lambda c: c['prisoner_number'] or '')))
            for (status_key, items) in grouped
        )
        grouped_credits[date] = grouped
    return grouped_credits.items()


@register.simple_tag
def credit_group_class(credit_status):
    if credit_status in ['credited', 'uncredited', 'refunded', 'anonymous']:
        return 'mtp-history-header__%s' % credit_status
    return ''


@register.filter
def sum_credits(credits):
    """
    Returns the total sum of credit amounts (irrespective of status)
    """
    return sum(map(lambda c: c['amount'] or 0, credits))


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


@register.filter
def truncate_user_list(terms):
    if len(terms) == 0:
        return _('No staff')
    elif len(terms) == 1:
        return terms[0]
    elif len(terms) == 2:
        return _('{name1} and {name2}').format(name1=terms[0], name2=terms[1])
    else:
        return _('{name} and {number} others').format(name=terms[0], number=len(terms) - 1)
