from django import template

register = template.Library()


@register.filter(is_safe=True)
def currency(value, symbol=None):
    if value is not None and value != '':
        format_str = '{:,.2f}'
        if symbol is not None:
            format_str = symbol + format_str
        return format_str.format(value / 100.)
    else:
        return None
