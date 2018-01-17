from django import template
from django.utils.translation import gettext_lazy as _

from disbursements.forms import SENDING_METHOD

register = template.Library()


@register.filter
def sendingmethod(method_key):
    return SENDING_METHOD.for_value(method_key).display


@register.filter
def format_sortcode(value):
    return '%s-%s-%s' % (value[0:2], value[2:4], value[4:6])


@register.filter
def format_disbursement_resolution(value):
    return {
        'pending': _('Waiting for confirmation'),
        'rejected': _('Cancelled'),
        'preconfirmed': _('Confirmed'),
        'confirmed': _('Confirmed'),
        'sent': _('Sent'),
    }.get(value, value)


@register.filter
def find_rejection_reason(comment_set):
    for comment in filter(lambda comment: comment['category'] == 'reject', comment_set):
        return comment['comment']
    return ''
