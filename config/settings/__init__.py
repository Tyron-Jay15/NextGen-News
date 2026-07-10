"""Settings package — loads environment-specific configuration."""
from decouple import config

ENV = config('DJANGO_ENV', default='development').lower()

if ENV in ('pythonanywhere', 'pa'):
    from .pythonanywhere import *  # noqa: F401, F403
elif ENV == 'production':
    from .production import *  # noqa: F401, F403
else:
    from .development import *  # noqa: F401, F403
