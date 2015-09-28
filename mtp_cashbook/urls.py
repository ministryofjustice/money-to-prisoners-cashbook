from django.conf.urls import patterns, include, url


urlpatterns = patterns(
    '',
    url(r'^', include('mtp_auth.urls', namespace='auth',)),
    url(r'^', include('cashbook.urls')),
)
