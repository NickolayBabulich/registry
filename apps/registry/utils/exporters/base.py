from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List


class BaseExporter(ABC):
    def __init__(self, document):
        self.document = document
        self.registry_schema = document.registry_schema

    def _format_field_value(self, value: Any, field_type: str) -> Any:
        """Форматирование значения поля в зависимости от его типа"""
        if field_type == "date" and value:
            try:
                return datetime.strptime(value, "%Y-%m-%d").strftime("%d.%m.%Y")
            except (ValueError, TypeError):
                return value
        elif field_type == "boolean":
            return "Да" if value else "Нет"
        elif field_type == "number" and value:
            try:
                return float(value)
            except (ValueError, TypeError):
                return value
        return value

    def _prepare_document_data(self) -> Dict:
        """Подготовка данных документа"""
        return {
            "document_id": self.document.id,
            "name": self.document.name,
            "schema": self.registry_schema.name,
            "schema_description": self.registry_schema.description,
            "created_by": self.document.created_by.get_full_name() or self.document.created_by.username,
            "created_at": self.document.created_at,
            "updated_at": self.document.updated_at,
            "fields": self._prepare_document_fields(),
        }

    def _prepare_document_fields(self) -> List[Dict]:
        """Подготовка полей документа"""
        fields_data = []
        for field in self.document.document_fields.all():
            formatted_data = {}
            for field_def in self.registry_schema.fields_schema:
                field_name = field_def["name"]
                field_type = field_def["type"]
                value = field.data.get(field_name)
                formatted_data[field_name] = self._format_field_value(value, field_type)

            field_data = {
                "id": field.id,
                "data": formatted_data,
            }
            fields_data.append(field_data)
        return fields_data

    def _get_field_headers(self) -> List[str]:
        """Получение заголовков полей из схемы"""
        return [field["name"] for field in self.registry_schema.fields_schema]

    def _get_field_types(self) -> Dict[str, str]:
        """Получение типов полей из схемы"""
        return {field["name"]: field["type"] for field in self.registry_schema.fields_schema}

    def generate_filename(self) -> str:
        """Генерация имени файла"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{self.document.name}_{timestamp}.{self.get_file_extension()}"

    @abstractmethod
    def get_file_extension(self) -> str:
        """Получение расширения файла"""

    @abstractmethod
    def export(self) -> Any:
        """Экспорт данных в соответствующий формат"""

    @abstractmethod
    def get_content_type(self) -> str:
        """Получение MIME-типа для HTTP-ответа"""


class ExporterFactory:
    """Фабрика для создания экспортеров"""

    @staticmethod
    def create_exporter(format_type: str, document):
        from .json_exporter import JsonExporter
        from .pdf_exporter import PdfExporter
        from .xlsx_exporter import XlsxExporter

        exporters = {
            "json": JsonExporter,
            "xlsx": XlsxExporter,
            "pdf": PdfExporter,
        }

        exporter_class = exporters.get(format_type)
        if not exporter_class:
            raise ValueError(f"Неподдерживаемый формат экспорта: {format_type}")

        return exporter_class(document)

    @staticmethod
    def get_supported_formats() -> List[str]:
        """Получение списка поддерживаемых форматов"""
        return ["json", "xlsx", "pdf"]
