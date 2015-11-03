from django.conf.urls import url
from django.core.urlresolvers import reverse_lazy

from moj_auth import views

urlpatterns = [
    url(r'^login/$', views.login, {
        'template_name': 'mtp_auth/login.html',
        }, name='login'),
    url(
        r'^logout/$', views.logout, {
            'template_name': 'mtp_auth/login.html',
            'next_page': reverse_lazy('login'),
        }, name='logout'
    ),
]
