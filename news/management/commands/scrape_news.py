"""Manually run the news scraper."""
from django.core.management.base import BaseCommand

from news.models import NewsSource
from news.scrapers.service import NewsScraperService


class Command(BaseCommand):
    help = 'Scrape RSS feeds and post new articles to your site'

    def add_arguments(self, parser):
        parser.add_argument('--source', type=int, help='Scrape only this source ID')
        parser.add_argument('--list', action='store_true', help='List active sources')

    def handle(self, *args, **options):
        if options['list']:
            for src in NewsSource.objects.all():
                status = 'active' if src.is_active else 'inactive'
                self.stdout.write(f'[{src.pk}] {src.name} ({status}) - {src.feed_url}')
            return

        source_id = options.get('source')
        if source_id:
            try:
                source = NewsSource.objects.get(pk=source_id)
            except NewsSource.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Source {source_id} not found'))
                return
            result = NewsScraperService.scrape_source(source)
            self.stdout.write(self.style.SUCCESS(
                f'{source.name}: {result["created"]} verified, {result["rejected"]} rejected, '
                f'{result["skipped"]} skipped, {result["errors"]} errors'
            ))
        else:
            self.stdout.write('Scraping all active trusted sources (credibility scan enabled)...')
            totals = NewsScraperService.scrape_all()
            self.stdout.write(self.style.SUCCESS(
                f'Done. Sources: {totals["sources"]}, '
                f'New verified: {totals["created"]}, '
                f'Rejected by scanner: {totals["rejected"]}, '
                f'Skipped: {totals["skipped"]}, '
                f'Errors: {totals["errors"]}'
            ))
