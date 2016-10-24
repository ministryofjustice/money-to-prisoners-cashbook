from decimal import Decimal

from django import template

register = template.Library()


@register.filter
def shortenint(value):
    try:
        if not isinstance(value, (float, Decimal)):
            value = int(value)
    except TypeError:
        return value

    if value >= 1000000:
        return '{:,.2f}'.format(value / 1000000).rstrip('0').rstrip('.') + 'm'
    if value >= 100000:
        return '{}k'.format(value // 1000)
    return '{:,}'.format(value)
