from .base import *

INSTALLED_APPS += ["rest_framework",
                   "django_filters",
                   'drf_spectacular',
                   "debug_toolbar",
                   "apps.registry.apps.RegistryConfig"]

MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]

INTERNAL_IPS = ["127.0.0.1"]

# AUTH_USER_MODEL = 'accounts.User'

ADMIN_EMAIL = env("ADMIN_EMAIL")
ADMIN_PASSWORD = env("ADMIN_PASSWORD")

# SECURITY
# ------------------------------------------------------------------------------
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False

# CORS HEADERS
# ------------------------------------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Registry API',
    'DESCRIPTION': 'API для управления реестрами документов',
    'VERSION': '0.2',
    'SERVE_INCLUDE_SCHEMA': False,

    # Настройки для улучшения документации
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api/v1',

    # Дополнительные теги для группировки endpoint'ов
    'TAGS': [
        {'name': 'registry-schemas', 'description': 'Операции со схемами реестров'},
        {'name': 'documents', 'description': 'Операции с документами'},
    ],

    # Настройки безопасности
    'SECURITY': [
        {'Bearer': []}
    ],
}

LOGIN_REDIRECT_URL = 'registry:documents'
LOGIN_URL = 'login'
LOGOUT_REDIRECT_URL = 'login'
