from django import forms

# <input type="text" class="form-control bfh-phone" data-format="+1 (ddd) ddd-dddd">
class PhoneWidget(forms.widgets.TextInput):
    def __init__(self, attrs=None, *args, **kwargs):
        attrs = attrs or {}

        default_options = {
            'type': 'text',
            'class': 'form-control bfh-phone',
            'data-format': '+1 (ddd) ddd-dddd',
        }
        options = kwargs.get('options', {})
        default_options.update(options)
        for key, val in default_options.items():
            attrs[key] = val

        super().__init__(attrs)
