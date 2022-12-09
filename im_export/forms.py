from django import forms
from django.core.validators import FileExtensionValidator


class ImportForm(forms.Form):
    import_file = forms.FileField(
        allow_empty_file=False,
        validators=[FileExtensionValidator(allowed_extensions=['csv', 'xls', 'xlsx'])], 
        label="")