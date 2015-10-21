from django.forms.widgets import TextInput, DateInput, \
    RadioFieldRenderer, RadioChoiceInput
from django.utils.html import format_html


class MtpInputMixin:
    css_classes = 'form-control'

    def build_attrs(self, extra_attrs=None, **kwargs):
        attrs = super().build_attrs(extra_attrs, **kwargs)
        attrs['class'] = attrs.get('class', '') + ' ' + self.css_classes
        return attrs


class MtpTextInput(MtpInputMixin, TextInput):
    pass


class MtpDateInput(MtpInputMixin, DateInput):
    css_classes = 'form-control js-FormDateControl'


class MtpRadioChoiceInput(RadioChoiceInput):
    def render(self, name=None, value=None, attrs=None, choices=()):
        if self.id_for_label:
            label_for = format_html(' for="{}"', self.id_for_label)
        else:
            label_for = ''
        attrs = dict(self.attrs, **attrs) if attrs else self.attrs
        return format_html(
            '<label class="block-label" {}>{} {}</label>', label_for, self.tag(attrs), self.choice_label
        )


class MtpRadioFieldRenderer(RadioFieldRenderer):
    choice_input_class = MtpRadioChoiceInput
    inner_html = '{choice_value}{sub_widgets}'
    outer_html = '<div {id_attr}>{content}</div>'


class MtpInlineRadioFieldRenderer(MtpRadioFieldRenderer):
    outer_html = '<div class="inline" {id_attr}>{content}</div>'
