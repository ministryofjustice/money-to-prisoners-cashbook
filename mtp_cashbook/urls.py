from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.urls import include, re_path
from django.views.decorators.cache import cache_control
from django.views.generic.base import RedirectView
from django.views.i18n import JavaScriptCatalog
from moj_irat.views import HealthcheckView, PingJsonView
from mtp_common.metrics.views import metrics_view

from mtp_cashbook import misc_views


urlpatterns = i18n_patterns(
    # dashboard / landing page
    re_path(r'^$', misc_views.LandingView.as_view(), name='home'),

    # miscellaneous views
    re_path(r'^faq/$', misc_views.FAQView.as_view(), name='faq'),
    re_path(r'^policy-change/$', misc_views.PolicyChangeInfo.as_view(), name='policy-change'),
    re_path(r'^ml-briefing/$', misc_views.MLBriefingConfirmationView.as_view(), name='ml-briefing-confirmation'),
    re_path(r'^ml-briefing/read/$', misc_views.MLBriefingView.as_view(), name='ml-briefing'),
    re_path(
        r'^confirm-credit-notice-emails/$', misc_views.ConfirmCreditNoticeEmailsView.as_view(),
        name='confirm-credit-notice-emails',
    ),

    # main applications
    re_path(r'^', include('cashbook.urls')),
    re_path(r'^disbursements/', include('disbursements.urls', namespace='disbursements')),

    # authentication and account management
    re_path(r'^', include('mtp_auth.urls')),
    re_path(r'^', include('mtp_common.user_admin.urls')),

    re_path(r'^', include('feedback.urls')),

    re_path(r'^settings/', include('settings.urls')),

    re_path(r'^js-i18n.js$', cache_control(public=True, max_age=86400)(JavaScriptCatalog.as_view()), name='js-i18n'),

    re_path(r'^404.html$', lambda request: TemplateResponse(request, 'mtp_common/errors/404.html', status=404)),
    re_path(r'^500.html$', lambda request: TemplateResponse(request, 'mtp_common/errors/500.html', status=500)),
)

urlpatterns += [
    re_path(r'^ping.json$', PingJsonView.as_view(
        build_date_key='APP_BUILD_DATE',
        commit_id_key='APP_GIT_COMMIT',
        version_number_key='APP_BUILD_TAG',
    ), name='ping_json'),
    re_path(r'^healthcheck.json$', HealthcheckView.as_view(), name='healthcheck_json'),
    re_path(r'^metrics.txt$', metrics_view, name='prometheus_metrics'),

    re_path(r'^favicon.ico$', RedirectView.as_view(url=settings.STATIC_URL + 'images/favicon.ico', permanent=True)),
    re_path(r'^robots.txt$', lambda request: HttpResponse('User-agent: *\nDisallow: /', content_type='text/plain')),
    re_path(r'^\.well-known/security\.txt$', RedirectView.as_view(
        url='https://security-guidance.service.justice.gov.uk/.well-known/security.txt',
        permanent=True,
    )),
]

handler404 = 'mtp_common.views.page_not_found'
handler500 = 'mtp_common.views.server_error'
handler400 = 'mtp_common.views.bad_request'
