"""
PythonAnywhere-friendly settings.

No Redis/Celery workers required. Use PA Scheduled Tasks for scrape_news.
Map /static/ and /media/ in the Web tab (SERVE_MEDIA is a fallback).
"""
from .base import *  # noqa: F401, F403

DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='.pythonanywhere.com,localhost,127.0.0.1',
    cast=Csv(),
)

CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='',
    cast=Csv(),
)

SITE_URL = config('SITE_URL', default='https://localhost')

# SQLite by default; set DB_ENGINE=mysql for a PythonAnywhere MySQL database
_db_engine = config('DB_ENGINE', default='sqlite').lower()
if _db_engine == 'mysql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST', default='yourusername.mysql.pythonanywhere-services.com'),
            'PORT': config('DB_PORT', default='3306'),
            'OPTIONS': {'charset': 'utf8mb4'},
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',  # noqa: F405
        }
    }

# No Redis on typical PythonAnywhere accounts
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'nextgen-news-pa',
    }
}
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

CHANNEL_LAYERS = {
    'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'},
}

# Run Celery tasks inline; schedule scrape via PA Tasks console instead of Celery Beat
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BEAT_SCHEDULE = {}

# Avoid Manifest static storage failures when a referenced file is missing
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# Fallback if /media/ is not mapped in the Web tab (prefer mapping it there)
SERVE_MEDIA = config('SERVE_MEDIA', default=True, cast=bool)

SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Ensure log directory exists before RotatingFileHandler opens
_logs_dir = BASE_DIR / 'logs'  # noqa: F405
_logs_dir.mkdir(parents=True, exist_ok=True)

LOGGING['root']['handlers'] = ['console', 'file']  # noqa: F405
