from .utils import nomis_integration_available


def nomis_integration(request):
    return {'nomis_integration_available': nomis_integration_available(request)}
