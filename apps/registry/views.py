from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.registry.forms import (
    DocumentAccessForm,
    DocumentCreateFromSchemaForm,
    DocumentEditForm,
    DocumentForm,
    RegistrySchemaForm,
)
from apps.registry.models import Document, DocumentAccess, DocumentField, RegistrySchema
from apps.registry.utils.exporters.base import ExporterFactory


class DocumentAccessMixin(UserPassesTestMixin):
    def test_func(self):
        obj = self.get_object()
        user = self.request.user

        if obj.created_by == user:
            return True

        access = DocumentAccess.objects.filter(document=obj, user=user).first()
        if not access:
            return False

        if self.__class__.__name__ in ["DocumentDetailView"]:
            return access.permission in ["view", "edit", "admin"]
        if self.__class__.__name__ in ["DocumentEditView"]:
            return access.permission in ["edit", "admin"]

        return False


class OwnerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        """Проверяет, является ли текущий пользователь владельцем объекта"""
        obj = self.get_object()

        # Если это схема реестра
        if isinstance(obj, RegistrySchema):
            return obj.owner == self.request.user

        # Если это документ
        elif isinstance(obj, Document):
            # Проверяем владельца документа и владельца схемы
            return (obj.created_by == self.request.user and
                    obj.registry_schema.owner == self.request.user)

        return False

    def handle_no_permission(self):
        messages.error(self.request, "У вас нет прав для выполнения этого действия")
        return redirect('registry:documents')

class RegistrySchemaListView(LoginRequiredMixin, ListView):
    model = RegistrySchema
    template_name = "registry/registry_schema/list.html"
    context_object_name = "registry_schemas"

    def get_queryset(self):
        # Возвращаем только схемы, принадлежащие текущему пользователю
        return RegistrySchema.objects.filter(
            owner=self.request.user
        ).select_related('owner').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_schemas_count'] = self.get_queryset().count()
        return context


class RegistrySchemaCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = RegistrySchema
    form_class = RegistrySchemaForm
    template_name = "registry/registry_schema/form.html"
    context_object_name = "registry_schema"
    success_url = reverse_lazy("registry:schemas")
    success_message = "Схема реестра успешно создана"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_create"] = True
        return context

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class RegistrySchemaEditView(LoginRequiredMixin, SuccessMessageMixin, OwnerRequiredMixin, UpdateView):
    model = RegistrySchema
    form_class = RegistrySchemaForm
    template_name = "registry/registry_schema/form.html"
    context_object_name = "registry_schema"
    success_url = reverse_lazy("registry:schemas")
    success_message = "Схема реестра успешно обновлена"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_create"] = False
        return context


class RegistrySchemaDeleteView(LoginRequiredMixin, SuccessMessageMixin, OwnerRequiredMixin, DeleteView):
    model = RegistrySchema
    success_url = reverse_lazy("registry:schemas")
    template_name = "registry/registry_schema/delete.html"
    context_object_name = "registry_schema"
    success_message = "Схема успешно удалена"

class DocumentListView(LoginRequiredMixin, ListView):
    model = Document
    template_name = "registry/document/list.html"
    context_object_name = "documents"

    def get_queryset(self):
        owned_documents = Document.objects.filter(created_by=self.request.user)
        shared_documents = Document.objects.filter(
            shared_access__user=self.request.user,
        )
        return owned_documents.union(shared_documents).order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        document_permissions = {}
        for document in context["documents"]:
            if document.created_by == self.request.user:
                document_permissions[document.id] = "owner"
            else:
                access = DocumentAccess.objects.get(
                    document=document,
                    user=self.request.user,
                )
                document_permissions[document.id] = access.permission
        context["document_permissions"] = document_permissions
        return context


class DocumentCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Document
    form_class = DocumentForm
    template_name = "registry/document/form.html"
    success_message = "Документ успешно создан"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Получаем схемы текущего пользователя
        user_schemas = RegistrySchema.objects.filter(owner=self.request.user)

        context.update({
            "entries": [],
            "registry_schema": None,
            "is_create": True,
            "available_schemas": user_schemas,  # Добавляем список доступных схем
            "has_schemas": user_schemas.exists(),  # Флаг наличия схем
        })
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("registry:document-detail", kwargs={"pk": self.object.id})


class DocumentCreateFromSchemaView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Document
    form_class = DocumentCreateFromSchemaForm
    template_name = "registry/document/form.html"
    success_message = "Документ успешно создан"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        # Проверяем, что схема принадлежит текущему пользователю
        self.registry_schema = get_object_or_404(
            RegistrySchema,
            id=self.kwargs["schema_id"],
            owner=self.request.user
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "entries": [],
            "registry_schema": self.registry_schema,
            "is_create": True,
        })
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.registry_schema = self.registry_schema
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("registry:document-detail", kwargs={"pk": self.object.id})


class DocumentDetailView(LoginRequiredMixin, DocumentAccessMixin, DetailView):
    model = Document
    template_name = "registry/document/detail.html"
    context_object_name = "document"

    def get_queryset(self):
        return Document.objects.filter(
            Q(created_by=self.request.user) |
            Q(shared_access__user=self.request.user)
        ).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user == self.object.created_by:
            context["user_permission"] = "owner"
        else:
            access = DocumentAccess.objects.get(
                document=self.object,
                user=self.request.user,
            )
            context["user_permission"] = access.permission
        return context


class DocumentEditView(LoginRequiredMixin, DocumentAccessMixin, SuccessMessageMixin, UpdateView):
    model = Document
    form_class = DocumentEditForm
    template_name = "registry/document/form.html"
    success_message = "Документ успешно обновлен"

    def get_queryset(self):
        return Document.objects.filter(
            Q(created_by=self.request.user) |
            Q(shared_access__user=self.request.user,
              shared_access__permission__in=["edit", "admin"])
        ).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user == self.object.created_by:
            user_permission = "owner"
        else:
            access = DocumentAccess.objects.get(
                document=self.object,
                user=self.request.user,
            )
            user_permission = access.permission

        context.update({
            "entries": self.object.document_fields.all(),
            "registry_schema": self.object.registry_schema,
            "document": self.object,
            "is_create": False,
            "user_permission": user_permission,
        })
        return context

    def form_valid(self, form):
        document = form.save(commit=False)
        document.save()

        self.object.document_fields.all().delete()
        i = 0

        while any(key.startswith(f"form-{i}-") for key in self.request.POST):
            entry_data = {}
            has_data = False

            for field in self.object.registry_schema.fields_schema:
                field_name = field["name"]
                field_value = self.request.POST.get(f"form-{i}-{field_name}")

                if field_value:
                    has_data = True
                    if field["type"] == "boolean":
                        entry_data[field_name] = field_value.lower() == "true"
                    elif field["type"] == "number":
                        try:
                            entry_data[field_name] = float(field_value)
                        except ValueError:
                            entry_data[field_name] = field_value
                    else:
                        entry_data[field_name] = field_value

            if has_data:
                DocumentField.objects.create(
                    document=document,
                    data=entry_data,
                )
            i += 1

        return super().form_valid(form)

    def get_success_url(self):
        return reverse("registry:document-detail", kwargs={"pk": self.object.id})


class DocumentDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Document
    template_name = "registry/document/delete.html"
    success_message = "Документ успешно удален"
    context_object_name = "document"

    def test_func(self):
        document = self.get_object()
        return self.request.user == document.created_by

    def get_success_url(self):
        return reverse("registry:documents")

class DocumentAccessView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        document = get_object_or_404(Document, pk=self.kwargs["pk"])
        return document.created_by == self.request.user

    def get(self, request, pk):
        document = get_object_or_404(Document, pk=pk)
        form = DocumentAccessForm(document=document)
        shared_users = DocumentAccess.objects.filter(document=document).select_related("user")

        return render(request, "registry/document/access.html", {
            "document": document,
            "form": form,
            "shared_users": shared_users,
        })

    def post(self, request, pk):
        document = get_object_or_404(Document, pk=pk)
        form = DocumentAccessForm(document=document, data=request.POST)

        if form.is_valid():
            access = form.save(commit=False)
            access.document = document
            access.created_by = request.user
            access.save()

            messages.success(
                request,
                "Доступ успешно предоставлен",
            )
            return redirect("registry:document-access", pk=pk)

        shared_users = DocumentAccess.objects.filter(document=document).select_related("user")
        return render(request, "registry/document/access.html", {
            "document": document,
            "form": form,
            "shared_users": shared_users,
        })


class DocumentAccessDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        document = get_object_or_404(Document, pk=self.kwargs["pk"])
        return document.created_by == self.request.user

    def post(self, request, pk, user_id):
        document = get_object_or_404(Document, pk=pk)
        DocumentAccess.objects.filter(document=document, user_id=user_id).delete()
        messages.success(request, "Доступ успешно отозван")
        return redirect("registry:document-access", pk=pk)

@login_required
def export_document(request, document_id, format_type="json"):
    document = get_object_or_404(
        Document.objects.filter(
            Q(created_by=request.user) |
            Q(shared_access__user=request.user,
              shared_access__permission__in=["view", "edit", "admin"]),
        ),
        id=document_id,
    )

    try:
        exporter = ExporterFactory.create_exporter(format_type, document)
        content = exporter.export()

        response = HttpResponse(
            content,
            content_type=exporter.get_content_type(),
        )
        response["Content-Disposition"] = f'attachment; filename="{exporter.generate_filename()}"'

        return response
    except ValueError as e:
        messages.error(request, str(e))
        return redirect("registry:document-detail", pk=document_id)
