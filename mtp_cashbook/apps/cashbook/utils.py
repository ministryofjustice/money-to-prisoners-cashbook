from django.conf import settings


class CashbookMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.pre_approval_required = self.pre_approval_required(request)
        request.disbursements_available = self.disbursements_available(request)
        request.disbursements_preview = self.disbursements_preview(request)
        return self.get_response(request)

    def pre_approval_required(self, request):
        return request.user.is_authenticated and any(
            prison['pre_approval_required']
            for prison in request.user.user_data.get('prisons', [])
        )

    def disbursements_available(self, request):
        return request.user.is_authenticated and any(
            prison['nomis_id'] in settings.DISBURSEMENT_PRISONS
            for prison in request.user.user_data.get('prisons', [])
        )

    def disbursements_preview(self, request):
        return request.user.is_authenticated and any(
            prison['nomis_id'] in settings.DISBURSEMENT_PREVIEW_PRISONS
            for prison in request.user.user_data.get('prisons', [])
        )
