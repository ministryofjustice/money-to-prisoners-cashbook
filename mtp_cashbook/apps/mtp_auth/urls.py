from django.conf.urls import url
from django.urls import reverse_lazy
from mtp_common.auth import views

urlpatterns = [
    url(
        r'^login/$', views.login, {
            'template_name': 'mtp_auth/login.html',
        }, name='login'
    ),
    url(
        r'^logout/$', views.logout, {
            'template_name': 'mtp_auth/login.html',
            'next_page': reverse_lazy('login'),
        }, name='logout'
    ),
    url(
        r'^password_change/$', views.password_change, {
            'template_name': 'mtp_common/auth/password_change.html',
            'cancel_url': reverse_lazy('new-credits'),
        }, name='password_change'
    ),
    url(
        r'^create_password/$', views.password_change_with_code, {
            'template_name': 'mtp_common/auth/password_change_with_code.html',
            'cancel_url': reverse_lazy('new-credits'),
        }, name='password_change_with_code'
    ),
    url(
        r'^password_change_done/$', views.password_change_done, {
            'template_name': 'mtp_common/auth/password_change_done.html',
            'cancel_url': reverse_lazy('new-credits'),
        }, name='password_change_done'
    ),
    url(
        r'^reset-password/$', views.reset_password, {
            'password_change_url': reverse_lazy('password_change_with_code'),
            'template_name': 'mtp_common/auth/reset-password.html',
            'cancel_url': reverse_lazy('new-credits'),
        }, name='reset_password'
    ),
    url(
        r'^reset-password-done/$', views.reset_password_done, {
            'template_name': 'mtp_common/auth/reset-password-done.html',
            'cancel_url': reverse_lazy('new-credits'),
        }, name='reset_password_done'
    ),
]
