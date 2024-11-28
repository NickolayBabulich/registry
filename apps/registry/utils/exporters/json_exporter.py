import json
from datetime import datetime

from .base import BaseExporter


class CustomJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%d.%m.%Y %H:%M:%S")
        return super().default(obj)


class JsonExporter(BaseExporter):
    def get_file_extension(self) -> str:
        return "json"

    def export(self) -> str:
        data = self._prepare_document_data()
        return json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
            cls=CustomJsonEncoder,
        )

    def get_content_type(self) -> str:
        return "application/json; charset=utf-8"
