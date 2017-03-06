from functools import wraps

from django.conf import settings
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import redirect


def nomis_integration_available(request):
    return settings.NOMIS_API_AVAILABLE and any((
        prison['nomis_id'] in settings.NOMIS_API_PRISONS
        for prison in request.user.user_data.get('prisons', [])
    ))


def require_nomis_integration(f):
    @wraps(f)
    def inner(request, *args, **kwargs):
        if not nomis_integration_available(request):
            return redirect(reverse_lazy('dashboard'))
        else:
            return f(request, *args, **kwargs)
    return inner
