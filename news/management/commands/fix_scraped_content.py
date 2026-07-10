"""Fix unreadable scraped articles and refresh BBC full text."""
from django.core.management.base import BaseCommand

from news.models import Article, NewsSource
from news.scrapers.parsers import build_summary_body, is_google_news_url
from news.scrapers.service import NewsScraperService


class Command(BaseCommand):
    help = 'Archive Google News stubs and refresh BBC article bodies with full text'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=0, help='Max BBC articles to refresh (0 = all)')

    def handle(self, *args, **options):
        NewsSource.objects.filter(name__icontains='Google News').update(is_active=False)
        NewsSource.objects.exclude(name__icontains='Google News').update(fetch_full_content=True)
        self.stdout.write('Disabled Google News sources; enabled full-content fetch for BBC feeds.')

        archived = Article.objects.filter(
            is_scraped=True,
            external_url__icontains='news.google.com',
        ).update(status='archived')
        self.stdout.write(f'Archived {archived} unreadable Google News article(s).')

        qs = Article.objects.filter(
            is_scraped=True,
            status='published',
            external_url__icontains='bbc.co.uk',
        ).order_by('-published_at')
        if options['limit']:
            qs = qs[:options['limit']]

        refreshed = 0
        failed = 0
        for article in qs:
            if NewsScraperService.refresh_article_body(article):
                refreshed += 1
            else:
                body = build_summary_body(article.title, article.excerpt)
                article.body = body + article.body[article.body.find('<hr>'):] if '<hr>' in article.body else body
                article.save(update_fields=['body'])
                failed += 1

        self.stdout.write(self.style.SUCCESS(
            f'Refreshed {refreshed} BBC article(s). {failed} kept summary fallback.'
        ))
