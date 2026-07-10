"""Set up default RSS news sources."""
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from categories.models import Category
from news.models import NewsSource


DEFAULT_SOURCES = [
    {
        'name': 'BBC World News',
        'feed_url': 'https://feeds.bbci.co.uk/news/world/rss.xml',
        'category': 'International',
        'attribution_name': 'BBC News',
    },
    {
        'name': 'BBC Technology',
        'feed_url': 'https://feeds.bbci.co.uk/news/technology/rss.xml',
        'category': 'Technology',
        'attribution_name': 'BBC News',
    },
    {
        'name': 'BBC Business',
        'feed_url': 'https://feeds.bbci.co.uk/news/business/rss.xml',
        'category': 'Business',
        'attribution_name': 'BBC News',
    },
    {
        'name': 'BBC Health',
        'feed_url': 'https://feeds.bbci.co.uk/news/health/rss.xml',
        'category': 'Health',
        'attribution_name': 'BBC News',
    },
    {
        'name': 'BBC Sport',
        'feed_url': 'https://feeds.bbci.co.uk/sport/rss.xml',
        'category': 'Sports',
        'attribution_name': 'BBC News',
    },
    {
        'name': 'Panay News',
        'feed_url': 'https://www.panaynews.net/feed',
        'category': 'Regional News',
        'attribution_name': 'Panay News',
        'province': 'Western Visayas',
    },
    {
        'name': 'Panay News - Iloilo',
        'feed_url': 'https://www.panaynews.net/category/news/iloilo/feed',
        'category': 'Regional News',
        'attribution_name': 'Panay News',
        'province': 'Iloilo',
    },
    {
        'name': 'Panay News - Negros',
        'feed_url': 'https://www.panaynews.net/category/news/negros/feed',
        'category': 'Regional News',
        'attribution_name': 'Panay News',
        'province': 'Negros Occidental',
    },
    {
        'name': 'Panay News - Region',
        'feed_url': 'https://www.panaynews.net/category/news/region/feed',
        'category': 'Regional News',
        'attribution_name': 'Panay News',
        'province': 'Western Visayas',
    },
    {
        'name': 'Panay News - Nation',
        'feed_url': 'https://www.panaynews.net/category/news/nation/feed',
        'category': 'Regional News',
        'attribution_name': 'Panay News',
        'province': 'Philippines',
    },
    {
        'name': 'Google News - Philippines',
        'feed_url': 'https://news.google.com/rss/search?q=Philippines&hl=en-PH&gl=PH&ceid=PH:en',
        'category': 'Regional News',
        'attribution_name': 'Google News',
        'is_active': False,
        'is_trusted': False,
    },
    {
        'name': 'Google News - Technology',
        'feed_url': 'https://news.google.com/rss/search?q=technology&hl=en-US&gl=US&ceid=US:en',
        'category': 'Technology',
        'attribution_name': 'Google News',
        'is_active': False,
        'is_trusted': False,
    },
]


class Command(BaseCommand):
    help = 'Create default RSS news sources for automatic scraping'

    def handle(self, *args, **options):
        created = 0
        for src in DEFAULT_SOURCES:
            cat, _ = Category.objects.get_or_create(
                slug=slugify(src['category']),
                defaults={'name': src['category'], 'is_active': True},
            )
            obj, was_created = NewsSource.objects.get_or_create(
                feed_url=src['feed_url'],
                defaults={
                    'name': src['name'],
                    'source_type': 'rss',
                    'category': cat,
                    'is_active': src.get('is_active', True),
                    'is_trusted': src.get('is_trusted', True),
                    'auto_publish': True,
                    'fetch_full_content': True,
                    'attribution_name': src['attribution_name'],
                },
            )
            if not was_created:
                obj.is_active = src.get('is_active', obj.is_active)
                obj.is_trusted = src.get('is_trusted', obj.is_trusted)
                obj.fetch_full_content = True
                obj.save(update_fields=['is_active', 'is_trusted', 'fetch_full_content'])
            if was_created:
                created += 1
                self.stdout.write(f'  + {src["name"]}')
        self.stdout.write(self.style.SUCCESS(f'Done. {created} new source(s) added.'))
