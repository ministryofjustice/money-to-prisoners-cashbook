from django.conf.urls import include, url

from moj_irat.views import HealthcheckView, PingJsonView

urlpatterns = [
    url(r'^', include('mtp_auth.urls')),
    url(r'^', include('cashbook.urls')),
    url(r'^', include('feedback.urls')),
    url(r'^', include('mtp_common.user_admin.urls')),

    url(r'^ping.json$', PingJsonView.as_view(
        build_date_key='APP_BUILD_DATE',
        commit_id_key='APP_GIT_COMMIT',
        version_number_key='APP_BUILD_TAG',
    ), name='ping_json'),
    url(r'^healthcheck.json$', HealthcheckView.as_view(), name='healthcheck_json'),
]

handler404 = 'mtp_common.views.page_not_found'
handler500 = 'mtp_common.views.server_error'
handler400 = 'mtp_common.views.bad_request'
