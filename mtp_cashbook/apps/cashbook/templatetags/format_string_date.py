from django import template
from django.conf import settings
from django.utils.dateformat import format
from django.utils.dateparse import parse_date, parse_datetime

register = template.Library()


@register.filter
def format_string_date(date_string, datetime_format=settings.DATETIME_FORMAT, date_format=settings.DATE_FORMAT):
    """
    MTP API responds with UTC date/time strings,
    this filter formats it according to the DATETIME_FORMAT/DATE_FORMAT settings
    """
    for parser, format_string in [[parse_datetime, datetime_format], [parse_date, date_format]]:
        try:
            parsed_date = parser(date_string)
            if not parsed_date:
                continue
            return format(parsed_date, format_string)
        except (ValueError, TypeError):
            continue
    return ''
