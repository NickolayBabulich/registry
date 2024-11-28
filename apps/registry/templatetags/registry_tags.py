from datetime import datetime

from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    if dictionary is None:
        return ""
    return dictionary.get(key, "")


@register.filter
def field_type_display(field_type):
    type_names = {
        "text": "Текст",
        "number": "Число",
        "date": "Дата",
        "boolean": "Логическое",
    }
    return type_names.get(field_type, field_type)


@register.filter
def format_date(value):
    if not value:
        return ""
    try:
        date_obj = datetime.fromisoformat(value)
        return date_obj.strftime("%d.%m.%Y")
    except (ValueError, TypeError):
        return value


@register.filter
def get_permission_display(permission):
    permission_displays = {
        "view": "Просмотр",
        "edit": "Редактирование",
        "admin": "Администрирование",
        "owner": "Владелец",
    }
    return permission_displays.get(permission, permission)


@register.filter
def permission_badge_color(permission):
    colors = {
        "view": "bg-secondary",  # Серый
        "edit": "bg-success",  # Зеленый
        "admin": "bg-purple",  # Фиолетовый
        "owner": "bg-primary",  # Синий
    }
    return colors.get(permission, "bg-secondary")
