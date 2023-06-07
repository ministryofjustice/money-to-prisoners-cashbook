from django import template
from django.utils.translation import gettext_lazy as _

from disbursements.forms import SendingMethod

register = template.Library()


@register.filter
def sendingmethod(method_key):
    return SendingMethod[method_key].label


@register.filter
def format_sortcode(value):
    return '%s-%s-%s' % (value[0:2], value[2:4], value[4:6])


@register.filter
def format_disbursement_action(value):
    return {
        'created': _('entered'),
        'edited': _('edited'),
        'rejected': _('cancelled'),
        'confirmed': _('confirmed'),
        'sent': _('sent'),
    }.get(value, value)


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
    for comment in filter(lambda c: c['category'] == 'reject', comment_set):
        return comment['comment']
    return ''
