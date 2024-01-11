from datetime import datetime
import logging

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, TemplateView
from mtp_common.analytics import genericised_pageview
from mtp_common.auth import api_client
from mtp_common import nomis
from requests.exceptions import RequestException

from cashbook.forms import (
    ProcessNewCreditsForm, ProcessManualCreditsForm,
    FilterProcessedCreditsListForm, FilterProcessedCreditsDetailForm,
    SearchForm, MANUALLY_CREDITED_LOG_LEVEL,
)
from feedback.views import GetHelpView, GetHelpSuccessView
from mtp_cashbook.misc_views import BaseView
from mtp_cashbook.utils import one_month_ago

logger = logging.getLogger('mtp')


class CashbookView(BaseView):
    def dispatch(self, request, *args, **kwargs):
        request.proposition_app = {
            'sub_app': 'cashbook',
            'name': _('Digital cashbook'),
            'url': reverse('new-credits'),
            'help_url': reverse('cashbook-faq'),
        }
        return super().dispatch(request, *args, **kwargs)


class CashbookFAQView(CashbookView, TemplateView):
    title = _('What do you need help with?')
    template_name = 'cashbook/faq.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['contact_us_url'] = reverse('cashbook_submit_ticket')
        context['fiu_email'] = settings.FIU_EMAIL
        context['noms_ops_url'] = settings.NOMS_OPS_URL
        context['send_money_url'] = settings.SEND_MONEY_URL

        return context


class CashbookGetHelpView(CashbookView, GetHelpView):
    base_template_name = 'cashbook/base.html'
    success_url = reverse_lazy('cashbook_feedback_success')


class CashbookGetHelpSuccessView(CashbookView, GetHelpSuccessView):
    base_template_name = 'cashbook/base.html'


class NewCreditsView(CashbookView, FormView):
    title = _('New credits')
    form_class = {
        'new': ProcessNewCreditsForm,
        'manual': ProcessManualCreditsForm
    }
    template_name = 'cashbook/new_credits.html'
    success_url = reverse_lazy('new-credits')

    def get_form(self, form_class=None):
        """
        Returns a dict of instances of the forms to be used in this view.
        """
        if form_class is None:
            form_class = self.get_form_class()
        return {
            name: form_class[name](**self.get_form_kwargs())
            for name in form_class
        }

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs['request'] = self.request
        if 'ordering' in self.request.GET:
            form_kwargs['ordering'] = self.request.GET['ordering']
        return form_kwargs

    def get(self, request, *args, **kwargs):
        session = api_client.get_api_session(self.request)
        batches = session.get('credits/batches/').json()
        if batches['count']:
            last_batch = batches['results'][0]
            credit_ids = last_batch['credits']
            incomplete_credits = session.get(
                'credits/', params={'resolution': 'pending', 'pk': credit_ids}
            ).json()
            if not last_batch['expired'] and incomplete_credits['count']:
                return redirect('processing-credits')

            credited_credits = session.get(
                'credits/', params={'resolution': 'credited', 'pk': credit_ids}
            ).json()
            kwargs['credited_credits'] = credited_credits['count']
            kwargs['failed_credits'] = incomplete_credits['count']
            session.delete(
                'credits/batches/{batch_id}/'.format(batch_id=last_batch['id'])
            )

        for message in messages.get_messages(request):
            if message.level == MANUALLY_CREDITED_LOG_LEVEL:
                kwargs['credited_manual_credits'] = int(message.message)

        return self.render_to_response(self.get_context_data(**kwargs))

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests, instantiating the relevant form instance with
        the passed POST variables and then checked for validity.
        """
        form_name = None
        for key in request.POST:
            for name in self.get_form_class():
                if key.startswith('submit_%s' % name):
                    form_name = name
        forms = self.get_form()
        if form_name in forms:
            form = forms[form_name]
            if form.is_valid():
                return self.form_valid(form)
        return self.form_invalid(None)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['start_page_url'] = settings.START_PAGE_URL

        new_credit_choices = context['form']['new'].credit_choices
        context['new_object_list'] = new_credit_choices
        context['total'] = sum([x[1]['amount'] for x in new_credit_choices])
        context['new_credits'] = len(new_credit_choices)

        manual_credit_choices = context['form']['manual'].credit_choices
        context['manual_credits'] = len(manual_credit_choices)

        owned_manual_credits = []
        unowned_manual_credits = []
        other_owners = set()
        unowned_oldest_date = None
        for credit_id, manual_credit in manual_credit_choices:
            try:
                location = nomis.get_location(manual_credit['prisoner_number'])
                manual_credit['new_location'] = location
            except RequestException:
                pass
            if manual_credit['owner'] == self.request.user.pk:
                owned_manual_credits.append((credit_id, manual_credit))
            else:
                unowned_manual_credits.append((credit_id, manual_credit))
                other_owners.add(manual_credit['owner_name'])
                if unowned_oldest_date is None or (
                        manual_credit['set_manual_at'] is not None and
                        unowned_oldest_date > manual_credit['set_manual_at']):
                    unowned_oldest_date = manual_credit['set_manual_at']

        context['owned_manual_object_list'] = owned_manual_credits
        context['owned_manual_credits'] = len(owned_manual_credits)

        context['unowned_manual_object_list'] = unowned_manual_credits
        context['unowned_manual_credits'] = len(unowned_manual_credits)
        context['other_owners'] = list(other_owners)
        context['unowned_oldest_date'] = unowned_oldest_date

        if context.get('credited_count', 0):
            username = self.request.user.user_data.get('username', 'Unknown')
            logger.info('User "%(username)s" added %(credited)d credits(s) to NOMIS', {
                'username': username,
                'credited': context['credited_count'],
            }, extra={
                'elk_fields': {
                    '@fields.credited_count': context['credited_count'],
                    '@fields.username': username,
                }
            })

        request_params = self.request.GET.dict()
        request_params.setdefault('ordering', '-received_at')
        context['request_params'] = request_params

        return context

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data())


class ProcessingCreditsView(CashbookView, TemplateView):
    title = _('Digital cashbook')
    template_name = 'cashbook/processing_credits.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        session = api_client.get_api_session(self.request)
        batches = session.get('credits/batches/').json()
        if batches['count'] == 0 or batches['results'][0]['expired']:
            return redirect('new-credits')
        else:
            credit_ids = batches['results'][0]['credits']
            total = len(credit_ids)
            incomplete_credits = session.get(
                'credits/', params={'resolution': 'pending', 'pk': credit_ids}
            ).json()
            done_credit_count = total - incomplete_credits['count']
            context['percentage'] = int((done_credit_count / total) * 100)
        return self.render_to_response(context)


class ProcessedCreditsListView(CashbookView, FormView):
    title = _('Processed credits')
    form_class = FilterProcessedCreditsListForm
    template_name = 'cashbook/processed_credits.html'
    success_url = reverse_lazy('processed-credits-list')

    def get_initial(self):
        initial = super().get_initial()
        initial.update({
            'page': 1,
            'start': one_month_ago().strftime('%d/%m/%Y'),
        })

        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        request_data = self.get_initial()
        request_data.update(self.request.GET.dict())
        kwargs['data'] = request_data
        kwargs['request'] = self.request
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        response['X-Frame-Options'] = 'SAMEORIGIN'
        return response

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_bound:
            if form.is_valid():
                return self.form_valid(form)
            else:
                return self.form_invalid(form)
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context['form']
        context.update({
            'object_list': list(form.credit_choices),
            'object_count': form.pagination['count'],
            'current_page': form.pagination['page'],
            'page_count': form.pagination['page_count'],
        })
        return context

    def form_valid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class ProcessedCreditsDetailView(ProcessedCreditsListView):
    title = _('Processed credits')
    form_class = FilterProcessedCreditsDetailForm
    template_name = 'cashbook/processed_credits_detail.html'
    success_url = reverse_lazy('processed-credits-detail')

    def get_form_kwargs(self):
        return dict(
            super().get_form_kwargs(),
            date=datetime.strptime(self.kwargs['date'], '%Y%m%d'),
            user_id=self.kwargs['user_id']
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total'] = sum(c['amount'] for c in context['object_list'])
        back_url = self.request.build_absolute_uri(str(ProcessedCreditsListView.success_url))
        referer_url = self.request.META.get('HTTP_REFERER') or ''
        if referer_url.startswith(back_url + '?'):
            back_url = referer_url
        context['breadcrumbs_back'] = back_url
        return context


class SearchView(CashbookView, FormView):
    title = _('Search all credits')
    form_class = SearchForm
    template_name = 'cashbook/search.html'
    success_url = reverse_lazy('search')

    def get_initial(self):
        initial = super().get_initial()
        initial.update({
            'page': 1,
            'start': one_month_ago().strftime('%d/%m/%Y'),
        })

        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        request_data = self.get_initial()
        request_data.update(self.request.GET.dict())
        kwargs['data'] = request_data
        kwargs['request'] = self.request
        return kwargs

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_bound:
            if form.is_valid():
                return self.form_valid(form)
            else:
                return self.form_invalid(form)
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context['form']
        search_field = form['search']
        new_credit_list = list(form.credit_choices)
        old_credit_list = []
        for index, credit in enumerate(new_credit_list):
            if credit['resolution'] == 'credited':
                new_credit_list, old_credit_list = new_credit_list[:index], new_credit_list[index:]
                break
        object_count = form.pagination['count']
        current_page = form.pagination['page']
        page_count = form.pagination['page_count']
        if form.is_valid() and form.cleaned_data.get('search'):
            self.title = _('Search for “%(query)s”') % {'query': form.cleaned_data['search']}
        context.update({
            'search_field': search_field,
            'new_credit_list': new_credit_list,
            'old_credit_list': old_credit_list,
            'credits_returned': form.is_valid() and (new_credit_list or old_credit_list),
            'form_has_errors': not form.is_valid(),
            'object_count': object_count,
            'current_page': current_page,
            'page_count': page_count,
            'credit_owner_name': self.request.user.get_full_name(),
            'google_analytics_pageview': genericised_pageview(
                self.request, SearchView.title
            )
        })
        return context

    def form_valid(self, form):
        return self.render_to_response(self.get_context_data(form=form))
