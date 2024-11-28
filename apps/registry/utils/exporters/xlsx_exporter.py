from io import BytesIO

import xlsxwriter

from .base import BaseExporter


class XlsxExporter(BaseExporter):
    def get_file_extension(self) -> str:
        return "xlsx"

    def get_content_type(self) -> str:
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    def export(self) -> bytes:
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)

        # Стили
        header_format = workbook.add_format({
            "bold": True,
            "bg_color": "#4F46E5",
            "font_color": "white",
            "border": 1,
            "align": "center",
            "valign": "vcenter",
            "text_wrap": True,
        })

        cell_format = workbook.add_format({
            "border": 1,
            "align": "left",
            "valign": "vcenter",
            "text_wrap": True,
        })

        bold_format = workbook.add_format({
            "bold": True,
            "align": "right",
        })

        # Создаем листы
        self._create_info_sheet(workbook, bold_format, cell_format)
        self._create_data_sheet(workbook, header_format, cell_format)

        workbook.close()
        output.seek(0)
        return output.getvalue()

    def _create_info_sheet(self, workbook, bold_format, cell_format):
        """Создание информационного листа"""
        info_sheet = workbook.add_worksheet("Информация")

        info_data = [
            ["Название документа:", self.document.name],
            ["Схема документа:", self.registry_schema.name],
            ["Создатель:", self.document.created_by.get_full_name()],
            ["Дата создания:", self.document.created_at.strftime("%d.%m.%Y %H:%M:%S")],
            ["Дата обновления:", self.document.updated_at.strftime("%d.%m.%Y %H:%M:%S")],
        ]

        if self.registry_schema.description:
            info_data.append(["Описание схемы:", self.registry_schema.description])

        # Записываем информацию о документе
        for row, (key, value) in enumerate(info_data):
            info_sheet.write(row, 0, key, bold_format)
            info_sheet.write(row, 1, value, cell_format)

        # Добавляем информацию о структуре полей
        row = len(info_data) + 2
        info_sheet.write(row, 0, "Структура полей:", bold_format)
        row += 1

        field_headers = ["Название поля", "Тип поля"]
        for col, header in enumerate(field_headers):
            info_sheet.write(row, col, header, bold_format)

        field_types = self._get_field_types()
        for field_name, field_type in field_types.items():
            row += 1
            field_type_name = {
                "text": "Текст",
                "number": "Число",
                "date": "Дата",
                "boolean": "Логическое значение",
            }.get(field_type, field_type)

            info_sheet.write(row, 0, field_name, cell_format)
            info_sheet.write(row, 1, field_type_name, cell_format)

        # Настройка ширины колонок
        info_sheet.set_column(0, 0, 20)
        info_sheet.set_column(1, 1, 40)

    def _create_data_sheet(self, workbook, header_format, cell_format):
        """Создание листа с данными"""
        data_sheet = workbook.add_worksheet("Данные документа")
        headers = self._get_field_headers()
        field_types = self._get_field_types()

        # Записываем заголовки
        for col, header in enumerate(headers):
            data_sheet.write(0, col, header, header_format)
            data_sheet.set_column(col, col, 20)  # Устанавливаем ширину для каждой колонки

        # Записываем данные
        row = 1
        for field in self.document.document_fields.all():
            for col, field_name in enumerate(headers):
                value = field.data.get(field_name, "")
                formatted_value = self._format_field_value(value, field_types[field_name])
                data_sheet.write(row, col, formatted_value, cell_format)
            row += 1
