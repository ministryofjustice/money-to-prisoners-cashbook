from django.conf.urls import patterns, url
from django.core.urlresolvers import reverse_lazy


urlpatterns = patterns('',
    url(r'^login/$', 'mtp_auth.views.login', name='login'),
    url(
        r'^logout/$', 'mtp_auth.views.logout', {
            'next_page': reverse_lazy('auth:login')
        }, name='logout'
    ),
)
