from django.conf import settings
from django.urls import reverse_lazy, re_path
from mtp_common.auth import views

from mtp_auth.views import CashbookSignUpView, CashbookAcceptRequestView, MovePrisonView

urlpatterns = [
    re_path(
        r'^login/$', views.login, {
            'template_name': 'mtp_auth/login.html',
            'extra_context': {
                'start_page_url': settings.START_PAGE_URL,
            },
        }, name='login',
    ),
    re_path(
        r'^logout/$', views.logout, {
            'template_name': 'mtp_auth/login.html',
            'next_page': reverse_lazy('login'),
        }, name='logout'
    ),

    re_path(
        r'^password_change/$', views.password_change, {
            'template_name': 'mtp_common/auth/password_change.html',
            'cancel_url': reverse_lazy('settings'),
        }, name='password_change'
    ),
    re_path(
        r'^create_password/$', views.password_change_with_code, {
            'template_name': 'mtp_common/auth/password_change_with_code.html',
            'cancel_url': reverse_lazy('home'),
        }, name='password_change_with_code'
    ),
    re_path(
        r'^password_change_done/$', views.password_change_done, {
            'template_name': 'mtp_common/auth/password_change_done.html',
            'cancel_url': reverse_lazy('home'),
        }, name='password_change_done'
    ),
    re_path(
        r'^reset-password/$', views.reset_password, {
            'password_change_url': reverse_lazy('password_change_with_code'),
            'template_name': 'mtp_common/auth/reset-password.html',
            'cancel_url': reverse_lazy('home'),
        }, name='reset_password'
    ),
    re_path(
        r'^reset-password-done/$', views.reset_password_done, {
            'template_name': 'mtp_common/auth/reset-password-done.html',
            'cancel_url': reverse_lazy('home'),
        }, name='reset_password_done'
    ),
    re_path(
        r'^email_change/$', views.email_change, {
            'cancel_url': reverse_lazy('settings'),
        }, name='email_change'
    ),

    re_path(r'^users/sign-up/$', CashbookSignUpView.as_view(), name='sign-up'),
    re_path(r'^users/move-prison/$', MovePrisonView.as_view(), name='move-prison'),
    re_path(
        r'^users/request/(?P<account_request>\d+)/accept/$',
        CashbookAcceptRequestView.as_view(),
        name='accept-request'
    ),
]
