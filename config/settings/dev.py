from .base import *

INSTALLED_APPS += ["debug_toolbar", "apps.registry.apps.RegistryConfig" ]

MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware" ]

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
