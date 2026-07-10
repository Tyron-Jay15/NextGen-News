"""Production settings (VPS / Docker with PostgreSQL + Redis)."""
from .base import *  # noqa: F401, F403

DEBUG = False

SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

_logs_dir = BASE_DIR / 'logs'  # noqa: F405
_logs_dir.mkdir(parents=True, exist_ok=True)

LOGGING['root']['handlers'] = ['console', 'file']  # noqa: F405
