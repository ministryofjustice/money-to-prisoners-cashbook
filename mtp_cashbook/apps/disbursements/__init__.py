from functools import wraps

from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse_lazy


def disbursements_available(request):
    return any((
        prison['nomis_id'] in settings.DISBURSEMENT_PRISONS
        for prison in request.user.user_data.get('prisons', [])
    ))


def disbursements_available_required(f):
    @wraps(f)
    def inner(request, *args, **kwargs):
        if disbursements_available(request):
            return f(request, *args, **kwargs)
        else:
            return redirect(reverse_lazy('home'))
    return inner
