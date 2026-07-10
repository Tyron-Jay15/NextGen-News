"""SEO sitemaps."""
from django.contrib.sitemaps import Sitemap
from django.utils import timezone

from categories.models import Category
from news.models import Article


class ArticleSitemap(Sitemap):
    changefreq = 'hourly'
    priority = 0.9

    def items(self):
        return Article.objects.filter(status='published', published_at__lte=timezone.now())

    def lastmod(self, obj):
        return obj.updated_at


class CategorySitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.7

    def items(self):
        return Category.objects.filter(is_active=True)


class GoogleNewsSitemap(Sitemap):
    changefreq = 'never'
    priority = 1.0
    limit = 1000

    def items(self):
        return Article.objects.filter(
            status='published',
            published_at__gte=timezone.now() - timezone.timedelta(days=2),
        ).order_by('-published_at')

    def lastmod(self, obj):
        return obj.published_at
