"""Remove demo/seed articles so only real scraped news remains."""
from django.core.management.base import BaseCommand

from news.models import Article


class Command(BaseCommand):
    help = 'Delete non-scraped demo articles (Lorem ipsum / seed data)'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Show count only, do not delete')

    def handle(self, *args, **options):
        demo_qs = Article.objects.filter(is_scraped=False)
        count = demo_qs.count()
        if options['dry_run']:
            self.stdout.write(f'Would delete {count} demo article(s).')
            return
        demo_qs.delete()
        self.stdout.write(self.style.SUCCESS(f'Removed {count} demo article(s). Live news only remains.'))
