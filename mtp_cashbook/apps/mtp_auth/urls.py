from django.conf.urls import patterns, url
from django.core.urlresolvers import reverse_lazy

from . import views

urlpatterns = patterns('',
    url(r'^login/$', views.login, name='login'),
    url(
        r'^logout/$', views.logout, {
            'next_page': reverse_lazy('auth:login'),
        }, name='logout'
    ),
)
