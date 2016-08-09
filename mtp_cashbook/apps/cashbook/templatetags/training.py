from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def get_training_page_template(context, page):
    view = context['view']
    return 'training/%s--%s.html' % (view.url_name, page)
