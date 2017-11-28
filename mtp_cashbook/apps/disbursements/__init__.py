from functools import wraps

from django.shortcuts import redirect
from django.urls import reverse


def disbursements_available_required(f):
    @wraps(f)
    def inner(request, *args, **kwargs):
        if request.disbursements_available:
            return f(request, *args, **kwargs)
        else:
            return redirect(reverse('home'))
    return inner
