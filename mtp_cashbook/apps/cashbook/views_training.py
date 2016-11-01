from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView


@method_decorator(login_required, name='dispatch')
class MultiPageView(TemplateView):
    template_name = 'training/page.html'
    training_title = NotImplemented
    url_name = NotImplemented
    pages = []
    next_training = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.page_set = {page['page'] for page in self.pages}

    def get(self, request, *args, **kwargs):
        page = kwargs['page']
        if not page:
            return redirect(self.url_name, page=self.pages[0]['page'])
        if page not in self.page_set:
            raise Http404('Training page %s not found' % page)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)

        current_page = kwargs['page']
        prev_page = None
        next_page = None
        for index, page in enumerate(self.pages):
            if page['page'] != current_page:
                continue
            if index > 0:
                prev_page = self.pages[index - 1]
            if index < len(self.pages) - 1:
                next_page = self.pages[index + 1]
            break

        kwargs.update({
            'current_page': current_page,
            'prev_page': prev_page,
            'next_page': next_page,
            'pages': self.pages,
            'breadcrumbs': [
                {'name': _('Home'), 'url': '/'},
                {'name': self.training_title}
            ],
            'start_page_url': settings.START_PAGE_URL,
        })
        return kwargs


class Training(MultiPageView):
    training_title = _('How to use the digital cashbook')
    url_name = 'training'
    pages = [
        {'page': 'intro',
         'title': _('Intro')},
        {'page': 'new',
         'title': _('New credits')},
        {'page': 'in-progress',
         'title': _('Credits being entered')},
        {'page': 'history',
         'title': _('All credits')},
    ]


class ServiceOverview(MultiPageView):
    training_title = _('Overview – sending money to prisoners online')
    url_name = 'service-overview'
    pages = [
        {'page': 'day-1',
         'title': _('Day 1')},
        {'page': 'day-2',
         'title': _('Day 2')},
        {'page': 'day-3',
         'title': _('Day 3')},
        {'page': 'day-4',
         'title': _('Day 4')},
        {'page': 'day-5',
         'title': _('Day 5')},
    ]
    next_training = Training
