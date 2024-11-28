import os
from io import BytesIO

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .base import BaseExporter

# Регистрируем шрифт
font_path = os.path.join(settings.BASE_DIR, "static", "fonts", "DejaVuSerif.ttf")
pdfmetrics.registerFont(TTFont("DejaVu", font_path))


class PdfExporter(BaseExporter):
    def get_file_extension(self) -> str:
        return "pdf"

    def get_content_type(self) -> str:
        return "application/pdf"

    def export(self) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30,
        )

        elements = []
        styles = self._get_styles()
        elements.extend(self._prepare_document_content(styles))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    def _get_styles(self):
        styles = getSampleStyleSheet()
        return {
            "title": ParagraphStyle(
                "CustomTitle",
                parent=styles["Heading1"],
                fontName="DejaVu",
                fontSize=16,
                spaceAfter=30,
                textColor=colors.HexColor("#4F46E5"),
            ),
            "heading2": ParagraphStyle(
                "CustomHeading2",
                parent=styles["Heading2"],
                fontName="DejaVu",
                fontSize=14,
                spaceAfter=20,
            ),
            "normal": ParagraphStyle(
                "CustomNormal",
                parent=styles["Normal"],
                fontName="DejaVu",
                fontSize=10,
                spaceAfter=10,
            ),
        }

    def _prepare_document_content(self, styles):
        elements = []

        # Заголовок документа
        elements.append(Paragraph(f"Документ: {self.document.name}", styles["title"]))
        elements.append(Spacer(1, 12))

        # Информация о документе
        info_data = [
            ["Схема документа:", self.registry_schema.name],
            ["Создатель:", self.document.created_by.get_full_name()],
            ["Дата создания:", self.document.created_at.strftime("%d.%m.%Y %H:%M:%S")],
            ["Дата обновления:", self.document.updated_at.strftime("%d.%m.%Y %H:%M:%S")],
        ]

        if self.registry_schema.description:
            info_data.append(["Описание схемы:", self.registry_schema.description])

        info_table = Table(info_data, colWidths=[120, 350])
        info_table.setStyle(self._get_table_style())
        elements.append(info_table)
        elements.append(Spacer(1, 20))

        # Структура полей
        elements.append(Paragraph("Структура полей документа:", styles["heading2"]))
        elements.append(Spacer(1, 12))

        field_types = self._get_field_types()
        fields_data = [["Название поля", "Тип поля"]]

        for field_name, field_type in field_types.items():
            field_type_name = {
                "text": "Текст",
                "number": "Число",
                "date": "Дата",
                "boolean": "Логическое значение",
            }.get(field_type, field_type)
            fields_data.append([field_name, field_type_name])

        fields_table = Table(fields_data, colWidths=[235, 235])
        fields_table.setStyle(self._get_table_style(has_header=True))
        elements.append(fields_table)
        elements.append(Spacer(1, 20))

        # Данные документа
        elements.append(Paragraph("Данные документа:", styles["heading2"]))
        elements.append(Spacer(1, 12))

        headers = self._get_field_headers()
        table_data = [headers]  # Заголовки полей

        # Добавляем данные
        for field in self.document.document_fields.all():
            row_data = []
            for field_name in headers:
                value = field.data.get(field_name, "")
                field_type = field_types[field_name]
                formatted_value = self._format_field_value(value, field_type)
                row_data.append(str(formatted_value))
            table_data.append(row_data)

        if len(table_data) > 1:
            # Вычисляем ширину колонок
            num_cols = len(headers)
            col_width = 470 / num_cols  # Общая ширина 470 делится на количество колонок
            doc_table = Table(table_data, colWidths=[col_width] * num_cols)
            doc_table.setStyle(self._get_table_style(has_header=True))
            elements.append(doc_table)
        else:
            elements.append(Paragraph("В документе нет записей", styles["normal"]))

        return elements

    def _get_table_style(self, has_header=False):
        style = [
            ("FONT", (0, 0), (-1, -1), "DejaVu"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]

        if has_header:
            style.extend([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4F46E5")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, 0), 11),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "DejaVu"),
            ])

        return TableStyle(style)
