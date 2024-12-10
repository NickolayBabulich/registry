from django.contrib.auth.models import User
from django.db import models

NULLABLE = {
    "blank": True,
    "null": True,
}


class RegistrySchema(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(**NULLABLE, verbose_name="Описание")
    fields_schema = models.JSONField(default=dict, verbose_name="Схема полей")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="registry_schema", db_index=True,
                              verbose_name="Владелец")

    class Meta:
        db_table = "registry_schema"
        verbose_name = "Схема реестра"
        verbose_name_plural = "Схемы реестров"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Document(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название")
    registry_schema = models.ForeignKey(RegistrySchema, on_delete=models.CASCADE, verbose_name="Схема реестра")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_documents",
                                   verbose_name="Создатель")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        db_table = "document"
        verbose_name = "Документ"
        verbose_name_plural = "Документы"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.registry_schema.name})"


class DocumentField(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="document_fields",
                                 verbose_name="Документ")
    data = models.JSONField(default=dict, verbose_name="Данные")

    class Meta:
        db_table = "document_fields"
        verbose_name = "Запись"
        verbose_name_plural = "Записи"

    def __str__(self):
        return f"Запись №{self.pk} в документе {self.document.name}"


class DocumentAccess(models.Model):
    PERMISSION_CHOICES = [
        ("view", "Просмотр"),
        ("edit", "Редактирование"),
        ("admin", "Администрирование"),
    ]

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="shared_access")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="document_accesses")
    permission = models.CharField(max_length=20, choices=PERMISSION_CHOICES, default="view")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="granted_document_accesses")

    class Meta:
        unique_together = ["document", "user"]
        verbose_name = "Доступ к документу"
        verbose_name_plural = "Доступы к документам"

    def __str__(self):
        return f"{self.user.username} - {self.document.name} ({self.get_permission_display()})"
