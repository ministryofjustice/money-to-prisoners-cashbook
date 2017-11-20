from django import template

from disbursements.forms import SENDING_METHOD

register = template.Library()


@register.filter
def sendingmethod(method_key):
    return SENDING_METHOD.for_value(method_key).display
