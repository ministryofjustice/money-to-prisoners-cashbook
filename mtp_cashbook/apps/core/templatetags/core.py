from django import template

register = template.Library()


@register.filter()
def to_string(value):
    return str(value)


@register.filter(is_safe=True)
def safewrap(val, arg):
    return val.format(arg)


@register.filter(name='addclass')
def addclass(element, className):
   return element.as_widget(attrs={"class":className})


@register.filter()
def field_from_name(form, name):
    if name in form.fields:
        return form[name]
