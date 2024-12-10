from typing import List, Dict, Any, Set
from datetime import datetime
import pandas as pd
from django.core.exceptions import ValidationError


class ColumnValidator:
    @staticmethod
    def validate_columns(expected: Set[str], actual: Set[str]) -> None:
        """Проверяет соответствие колонок Excel ожидаемой схеме."""
        if expected != actual:
            missing = expected - actual
            extra = actual - expected
            raise ValidationError(
                f"Несоответствие колонок в файле.\n"
                f"Отсутствующие колонки: {', '.join(missing) if missing else 'нет'}\n"
                f"Лишние колонки: {', '.join(extra) if extra else 'нет'}"
            )


class ValueConverter:
    @staticmethod
    def convert_date(value: Any) -> str:
        """Конвертирует значение в формат даты."""
        if isinstance(value, str):
            return datetime.strptime(value, '%d.%m.%Y').strftime('%Y-%m-%d')
        return value.strftime('%Y-%m-%d')

    @staticmethod
    def convert_number(value: Any) -> float:
        """Конвертирует значение в число."""
        return float(value)

    @staticmethod
    def convert_boolean(value: Any) -> bool:
        """Конвертирует значение в булево значение."""
        if isinstance(value, str):
            return value.lower() == 'да'
        return bool(value)

    @staticmethod
    def convert_string(value: Any) -> str:
        """Конвертирует значение в строку."""
        return str(value)


class DataConverter:
    def __init__(self, field_types: Dict[str, str]):
        self.field_types = field_types
        self.type_converters = {
            'date': ValueConverter.convert_date,
            'number': ValueConverter.convert_number,
            'boolean': ValueConverter.convert_boolean,
            'string': ValueConverter.convert_string
        }

    def convert_field_value(self, field_name: str, value: Any) -> Any:
        """Конвертирует значение поля в соответствии с его типом."""
        if pd.isna(value):
            return None

        field_type = self.field_types[field_name]
        converter = self.type_converters.get(field_type, ValueConverter.convert_string)

        try:
            return converter(value)
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Ошибка конвертации значения в поле '{field_name}': {str(e)}")


class ExcelTemplateImporter:
    def __init__(self, registry_schema):
        """Инициализация импортера с заданной схемой реестра."""
        self.registry_schema = registry_schema
        self.field_types = {field['name']: field['type'] for field in registry_schema.fields_schema}
        self.data_converter = DataConverter(self.field_types)

    def read_excel_file(self, file_content: bytes) -> pd.DataFrame:
        """Читает Excel файл в DataFrame."""
        return pd.read_excel(
            file_content,
            sheet_name='Данные',
            engine='openpyxl'
        )

    def convert_row_to_record(self, row: pd.Series) -> Dict[str, Any]:
        """Конвертирует строку DataFrame в запись."""
        record = {}
        for field_name in self.field_types:
            converted_value = self.data_converter.convert_field_value(field_name, row[field_name])
            if converted_value is not None:
                record[field_name] = converted_value
        return record

    def parse_excel(self, file_content: bytes) -> List[Dict[str, Any]]:
        """Основной метод для парсинга Excel файла."""
        try:
            df = self.read_excel_file(file_content)

            # Валидация колонок
            ColumnValidator.validate_columns(
                set(self.field_types.keys()),
                set(df.columns)
            )

            # Конвертация данных
            records = []
            for _, row in df.iterrows():
                record = self.convert_row_to_record(row)
                if record:  # Добавляем только непустые записи
                    records.append(record)

            return records

        except Exception as e:
            raise ValidationError(f"Ошибка при обработке файла: {str(e)}")