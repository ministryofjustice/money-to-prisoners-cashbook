from functools import wraps

from django.conf import settings
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import redirect


def check_pre_approval_required(request):
    return any((
        prison['pre_approval_required']
        for prison in request.user.user_data.get('prisons', [])
    ))


def nomis_integration_available(request):
    return settings.NOMIS_API_AVAILABLE and any((
        prison['nomis_id'] in settings.NOMIS_API_PRISONS
        for prison in request.user.user_data.get('prisons', [])
    ))


def expected_nomis_availability(expectation):
    def decorator(f):
        @wraps(f)
        def inner(request, *args, **kwargs):
            if nomis_integration_available(request) != expectation:
                return redirect(reverse_lazy('dashboard'))
            else:
                return f(request, *args, **kwargs)
        return inner
    return decorator
