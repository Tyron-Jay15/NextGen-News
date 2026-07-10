"""Re-download sharp hero images from publisher pages for existing articles."""
from django.core.management.base import BaseCommand

from news.models import Article
from news.scrapers.service import NewsScraperService
from news.utils.placeholders import assign_hero_image


class Command(BaseCommand):
    help = 'Refresh hero images by re-downloading high-resolution photos from source pages'

    def add_arguments(self, parser):
        parser.add_argument('--scraped-only', action='store_true', help='Only refresh scraped articles')
        parser.add_argument('--placeholders-only', action='store_true', help='Regenerate placeholder images only')
        parser.add_argument('--limit', type=int, default=0, help='Max articles to process (0 = all)')

    def handle(self, *args, **options):
        qs = Article.objects.filter(status='published').order_by('-published_at')
        if options['scraped_only']:
            qs = qs.filter(is_scraped=True)

        if options['limit']:
            qs = qs[:options['limit']]

        updated = 0
        placeholders = 0
        failed = 0

        for i, article in enumerate(qs.iterator()):
            if options['placeholders_only'] or not article.external_url:
                if assign_hero_image(article, index=i, force=True):
                    placeholders += 1
                continue

            if NewsScraperService.refresh_hero_image(article):
                updated += 1
            elif assign_hero_image(article, index=i, force=True):
                placeholders += 1
            else:
                failed += 1

        self.stdout.write(self.style.SUCCESS(
            f'Images updated: {updated} from source, {placeholders} placeholders, {failed} unchanged.'
        ))
