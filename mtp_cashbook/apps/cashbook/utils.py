class CashbookMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.pre_approval_required = self.pre_approval_required(request)
        return self.get_response(request)

    def pre_approval_required(self, request):
        return request.user.is_authenticated and any(
            prison['pre_approval_required']
            for prison in request.user.user_data.get('prisons', [])
        )
