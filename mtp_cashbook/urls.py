from django.conf.urls import include, url

urlpatterns = [
    url(r'^', include('mtp_auth.urls')),
    url(r'^', include('cashbook.urls')),
    url(r'^', include('feedback.urls')),
]
