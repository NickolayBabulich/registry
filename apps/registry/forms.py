from datetime import date
from decimal import Decimal

from django import forms
from django.contrib.auth.models import User

from apps.registry.models import Document, DocumentAccess, DocumentField, RegistrySchema


class RegistrySchemaForm(forms.ModelForm):
    class Meta:
        model = RegistrySchema
        fields = ["name", "description", "fields_schema"]
        widgets = {
            "fields_schema": forms.HiddenInput(),
        }


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ["name", "registry_schema"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Введите название документа",
                "required": True,
            }),
            "registry_schema": forms.Select(attrs={
                "class": "form-select",
                "required": True,
            }),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['registry_schema'].queryset = RegistrySchema.objects.filter(owner=user)
            self.fields['registry_schema'].empty_label = "Выберите схему документа"


class DocumentCreateFromSchemaForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Введите название документа",
                "required": True,
            }),
        }


class DocumentEditForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Введите название документа",
                "required": True,
            }),
        }


class DocumentFieldForm(forms.ModelForm):
    class Meta:
        model = DocumentField
        fields = []

    def __init__(self, *args, registry_schema=None, instance=None, **kwargs):
        super().__init__(*args, instance=instance, **kwargs)
        if registry_schema and registry_schema.fields_schema:
            for field in registry_schema.fields_schema:
                field_name = field['name']
                field_type = field['type']
                field_value = instance.data.get(field_name) if instance else None

                if field_type == 'text':
                    self.fields[field_name] = forms.CharField(
                        required=False,
                        initial=field_value,
                        widget=forms.TextInput(attrs={'class': 'form-control'})
                    )
                elif field_type == 'number':
                    self.fields[field_name] = forms.DecimalField(
                        required=False,
                        initial=field_value,
                        widget=forms.NumberInput(attrs={'class': 'form-control'})
                    )
                elif field_type == 'date':
                    self.fields[field_name] = forms.DateField(
                        required=False,
                        initial=field_value,
                        widget=forms.DateInput(attrs={
                            'class': 'form-control',
                            'type': 'date'
                        })
                    )
                elif field_type == 'boolean':
                    self.fields[field_name] = forms.BooleanField(
                        required=False,
                        initial=field_value,
                        widget=forms.Select(
                            attrs={'class': 'form-select'},
                            choices=((True, 'Да'), (False, 'Нет'))
                        )
                    )

    def clean(self):
        cleaned_data = super().clean()
        data = {}

        if hasattr(self, 'registry_schema') and self.registry_schema:
            field_schema = self.registry_schema.fields_schema
            if isinstance(field_schema, list):
                for field_def in field_schema:
                    field_name = field_def['name']
                    if field_name in cleaned_data:
                        value = cleaned_data[field_name]
                        if value is not None:
                            if isinstance(value, date):
                                value = value.isoformat()
                            elif isinstance(value, Decimal):
                                value = float(value)
                            data[field_name] = value

        return {'data': data}


class DocumentAccessForm(forms.ModelForm):
    user = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label="Пользователь",
        widget=forms.Select(attrs={
            "class": "form-select",
            "placeholder": "Выберите пользователя",
        }),
    )

    class Meta:
        model = DocumentAccess
        fields = ["user", "permission"]
        widgets = {
            "permission": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, document, *args, **kwargs):
        super().__init__(*args, **kwargs)

        existing_users = DocumentAccess.objects.filter(
            document=document
        ).values_list("user", flat=True)

        self.fields["user"].queryset = User.objects.exclude(
            id__in=[document.created_by.id, *existing_users],
        ).order_by("username")

        self.fields["user"].help_text = "Выберите пользователя, которому хотите предоставить доступ"
        self.fields["permission"].help_text = "Выберите уровень доступа для пользователя"
