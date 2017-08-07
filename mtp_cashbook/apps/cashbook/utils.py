def check_pre_approval_required(request):
    return any((
        prison['pre_approval_required']
        for prison in request.user.user_data.get('prisons', [])
    ))
