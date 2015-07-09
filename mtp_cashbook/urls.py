from django.conf.urls import patterns, include, url
from django.contrib.auth.decorators import login_required
from django.views.generic.base import TemplateView

urlpatterns = patterns(
    '',
    url(
        r'^$',
        login_required(
            TemplateView.as_view(template_name='core/index.html')
        ),
        name='index'
    ),

    url(r'^auth/', include('mtp_auth.urls', namespace='auth',)),
)
