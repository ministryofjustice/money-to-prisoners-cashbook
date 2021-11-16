from mtp_cashbook import READ_ML_BRIEFING_FLAG


class CashbookMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.read_ml_briefing = self.read_ml_briefing(request)
        request.pre_approval_required = self.pre_approval_required(request)
        return self.get_response(request)

    @staticmethod
    def read_ml_briefing(request):
        return (
            request.user.is_authenticated
            and READ_ML_BRIEFING_FLAG in (request.user.user_data.get('flags') or ())
        )

    @staticmethod
    def pre_approval_required(request):
        return request.user.is_authenticated and any(
            prison['pre_approval_required']
            for prison in request.user.user_data.get('prisons', [])
        )
