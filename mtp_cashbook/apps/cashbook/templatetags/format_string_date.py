from django import template
from django.conf import settings
from django.utils.dateformat import format
from django.utils.dateparse import parse_datetime

register = template.Library()


@register.filter
def format_string_date(date_string, format_string=settings.DATETIME_FORMAT):
    """
    MTP API responds with UTC date strings,
    this filter formats it according to the DATETIME_FORMAT settings
    """
    try:
        datetime = parse_datetime(date_string)
        return format(datetime, format_string)
    except (ValueError, TypeError):
        return ''
