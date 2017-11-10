from django import template

from disbursements.forms import ACCOUNTS

register = template.Library()


@register.filter
def accountlabel(account_key):
    return ACCOUNTS.get(account_key)
