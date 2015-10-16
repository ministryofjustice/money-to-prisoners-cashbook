from collections import OrderedDict
from itertools import groupby

from django import template

register = template.Library()


@register.filter
def regroup_transactions(transactions):
    """
    Groups transactions into days (by received_at) and refunded status
    """
    def is_refunded(t):
        return t['refunded']

    grouped_transactions = OrderedDict()
    groups = groupby(transactions, key=lambda t: t['received_at'][:10] if 'received_at' in t else None)
    for date, group in groups:
        grouped = groupby(sorted(group, key=is_refunded), key=is_refunded)
        grouped = [(key, list(items)) for (key, items) in grouped]  # so that it can be iterated multiple times
        grouped_transactions[date] = grouped
    return grouped_transactions.items()


@register.filter
def sum_transactions(transactions):
    """
    Returns the total sum of payment amounts (irrespective of status)
    """
    return sum(map(lambda t: t['amount'] or 0, transactions))
