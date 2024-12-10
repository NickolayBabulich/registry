from io import BytesIO
import xlsxwriter
from typing import Dict, List


class ExcelFormatManager:
    """Управление форматами Excel."""

    def __init__(self, workbook: xlsxwriter.Workbook):
        self.workbook = workbook

    def create_header_format(self) -> xlsxwriter.format.Format:
        """Создает формат для заголовков."""
        return self.workbook.add_format({
            'bold': True,
            'bg_color': '#D9D9D9',
            'border': 1,
            'text_wrap': True,
            'locked': True,
        })

    def create_unlocked_format(self) -> xlsxwriter.format.Format:
        """Создает формат для разблокированных ячеек."""
        return self.workbook.add_format({
            'locked': False,
            'border': 1
        })

    def create_date_format(self) -> xlsxwriter.format.Format:
        """Создает формат для дат."""
        return self.workbook.add_format({
            'num_format': 'dd.mm.yyyy',
            'locked': False,
            'border': 1
        })

    def create_number_format(self) -> xlsxwriter.format.Format:
        """Создает формат для чисел."""
        return self.workbook.add_format({
            'num_format': '0.00',
            'locked': False,
            'border': 1
        })


class InfoSheetManager:
    """Управление информационным листом."""

    def __init__(self, workbook: xlsxwriter.Workbook, document_name: str, schema_name: str):
        self.workbook = workbook
        self.document_name = document_name
        self.schema_name = schema_name

    def create_info_sheet(self) -> None:
        """Создает информационный лист."""
        info_sheet = self.workbook.add_worksheet('Информация')
        info_sheet.protect()

        self._write_document_info(info_sheet)
        self._write_instructions(info_sheet)

    def _write_document_info(self, sheet: xlsxwriter.worksheet.Worksheet) -> None:
        """Записывает информацию о документе."""
        sheet.write(0, 0, f"Документ: {self.document_name}")
        sheet.write(1, 0, f"Схема: {self.schema_name}")

    def _write_instructions(self, sheet: xlsxwriter.worksheet.Worksheet) -> None:
        """Записывает инструкции по заполнению."""
        instructions = [
            "Инструкция по заполнению:",
            "1. Заполняйте данные на листе 'Данные'",
            "2. Названия и порядок столбцов изменять нельзя",
            "3. Добавлять новые столбцы нельзя",
            "4. Данные вносите начиная со второй строки"
        ]
        for i, instruction in enumerate(instructions, start=3):
            sheet.write(i, 0, instruction)


class DataSheetManager:
    """Управление листом данных."""

    def __init__(self, workbook: xlsxwriter.Workbook, format_manager: ExcelFormatManager):
        self.workbook = workbook
        self.format_manager = format_manager
        self.max_rows = 1000

    def create_data_sheet(self, fields_schema: List[Dict[str, str]]) -> xlsxwriter.worksheet.Worksheet:
        """Создает лист данных."""
        data_sheet = self.workbook.add_worksheet('Данные')
        self._set_sheet_protection(data_sheet)
        self._setup_columns(data_sheet, fields_schema)
        self._setup_working_area(data_sheet, len(fields_schema))
        return data_sheet

    def _set_sheet_protection(self, sheet: xlsxwriter.worksheet.Worksheet) -> None:
        """Устанавливает защиту листа."""
        sheet.protect('', {
            'format_cells': False,
            'format_columns': False,
            'format_rows': False,
            'insert_columns': False,
            'delete_columns': False,
            'insert_rows': True,
            'delete_rows': True,
            'sort': True,
            'autofilter': True,
            'edit_objects': False,
            'select_locked_cells': True,
            'select_unlocked_cells': True,
        })

    def _setup_columns(self, sheet: xlsxwriter.worksheet.Worksheet, fields_schema: List[Dict[str, str]]) -> None:
        """Настраивает столбцы и их форматирование."""
        header_format = self.format_manager.create_header_format()

        for col, field in enumerate(fields_schema):
            self._setup_single_column(sheet, col, field, header_format)

    def _setup_single_column(self, sheet: xlsxwriter.worksheet.Worksheet, col: int, field: Dict[str, str],
                             header_format: xlsxwriter.format.Format) -> None:
        """Настраивает отдельный столбец."""
        column_name = field['name']
        field_type = field['type']

        sheet.write(0, col, column_name, header_format)

        if field_type == 'date':
            self._setup_date_column(sheet, col)
        elif field_type == 'number':
            self._setup_number_column(sheet, col)
        elif field_type == 'boolean':
            self._setup_boolean_column(sheet, col)
        else:
            self._setup_text_column(sheet, col)

    def _setup_date_column(self, sheet: xlsxwriter.worksheet.Worksheet, col: int) -> None:
        """Настраивает столбец с датами."""
        date_format = self.format_manager.create_date_format()
        sheet.set_column(col, col, 15, date_format)
        sheet.data_validation(1, col, self.max_rows, col, {
            'validate': 'date',
            'criteria': 'between',
            'minimum': '=DATE(2000,1,1)',
            'maximum': '=DATE(2099,12,31)',
        })

    def _setup_number_column(self, sheet: xlsxwriter.worksheet.Worksheet, col: int) -> None:
        """Настраивает столбец с числами."""
        number_format = self.format_manager.create_number_format()
        sheet.set_column(col, col, 12, number_format)

    def _setup_boolean_column(self, sheet: xlsxwriter.worksheet.Worksheet, col: int) -> None:
        """Настраивает столбец с логическими значениями."""
        unlocked_format = self.format_manager.create_unlocked_format()
        sheet.data_validation(1, col, self.max_rows, col, {
            'validate': 'list',
            'source': ['Да', 'Нет']
        })
        sheet.set_column(col, col, 10, unlocked_format)

    def _setup_text_column(self, sheet: xlsxwriter.worksheet.Worksheet, col: int) -> None:
        """Настраивает столбец с текстом."""
        unlocked_format = self.format_manager.create_unlocked_format()
        sheet.set_column(col, col, 20, unlocked_format)

    def _setup_working_area(self, sheet: xlsxwriter.worksheet.Worksheet, last_col_index: int) -> None:
        """Настраивает рабочую область."""
        last_col = last_col_index - 1
        sheet.set_selection(f'A2:${xlsxwriter.utility.xl_col_to_name(last_col)}2')

        if last_col + 1 < 16384:
            sheet.set_column(last_col + 1, 16384, None, None, {'hidden': True})


class DocumentTemplateGenerator:
    """Основной класс генератора шаблонов документов."""

    def __init__(self, document):
        self.document = document
        self.registry_schema = document.registry_schema
        self.output = BytesIO()
        self.workbook = xlsxwriter.Workbook(self.output)
        self.format_manager = ExcelFormatManager(self.workbook)

    def generate(self) -> BytesIO:
        """Генерирует шаблон документа."""
        # Создаем информационный лист
        info_manager = InfoSheetManager(
            self.workbook,
            self.document.name,
            self.registry_schema.name
        )
        info_manager.create_info_sheet()

        # Создаем лист данных
        data_manager = DataSheetManager(self.workbook, self.format_manager)
        data_manager.create_data_sheet(self.registry_schema.fields_schema)

        # Закрываем и возвращаем файл
        self.workbook.close()
        self.output.seek(0)
        return self.output
