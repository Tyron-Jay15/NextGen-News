"""Template context processors."""
from django.conf import settings

from dashboard.models import SiteSetting


def site_settings(request):
    """Inject site-wide settings into templates."""
    try:
        settings_obj = SiteSetting.load()
    except Exception:
        settings_obj = None
    return {
        'site_name': settings.SITE_NAME,
        'site_url': settings.SITE_URL,
        'brand_colors': settings.BRAND_COLORS,
        'site_settings': settings_obj,
    }


def navigation(request):
    """Inject navigation data for mega menu."""
    from categories.models import Category
    from news.models import Article

    categories = Category.objects.filter(is_active=True, parent__isnull=True).prefetch_related('children')[:12]
    breaking = Article.objects.filter(status='published', is_breaking=True).order_by('-published_at')[:5]
    return {
        'nav_categories': categories,
        'breaking_news': breaking,
    }
