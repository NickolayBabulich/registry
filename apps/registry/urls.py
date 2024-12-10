from django.urls import path

from apps.registry import views

app_name = "registry"

urlpatterns = [
    # Схемы реестров
    path("registry-schemas/",
         views.RegistrySchemaListView.as_view(),
         name="schemas"),
    path("registry-schemas/create/",
         views.RegistrySchemaCreateView.as_view(),
         name="schema-create"),
    path("register-schemas/<int:pk>/edit/",
         views.RegistrySchemaEditView.as_view(),
         name="schema-edit"),
    path("registry-schemas/<int:pk>/delete/",
         views.RegistrySchemaDeleteView.as_view(),
         name="schema-delete"),

    # Документы
    path("documents/",
         views.DocumentListView.as_view(),
         name="documents"),
    path("documents/create/",
         views.DocumentCreateView.as_view(),
         name="document-create"),
    path("documents/create/<int:schema_id>/",
         views.DocumentCreateFromSchemaView.as_view(),
         name="document-create-from-schema"),
    path("documents/<int:pk>/",
         views.DocumentDetailView.as_view(),
         name="document-detail"),
    path("documents/<int:pk>/edit/",
         views.DocumentEditView.as_view(),
         name="document-edit"),
    path("documents/<int:pk>/delete/",
         views.DocumentDeleteView.as_view(),
         name="document-delete"),

    # Управление доступом к документам
    path("documents/<int:pk>/access/",
         views.DocumentAccessView.as_view(),
         name="document-access"),
    path("documents/<int:pk>/access/<int:user_id>/delete/",
         views.DocumentAccessDeleteView.as_view(),
         name="document-access-delete"),

    # Экспорт
    path("documents/<int:document_id>/export/<str:format_type>/",
         views.export_document,
         name="document-export"),

    path("documents/<int:pk>/template/",
         views.DocumentTemplateView.as_view(),
         name="document-template"),
    path("documents/<int:pk>/import/",
         views.DocumentImportView.as_view(),
         name="document-import"),
]
