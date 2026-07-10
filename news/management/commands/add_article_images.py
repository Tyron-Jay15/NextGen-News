"""Add hero images to articles that don't have one."""
from django.core.management.base import BaseCommand

from news.models import Article
from news.utils.placeholders import assign_hero_image


class Command(BaseCommand):
    help = 'Generate and assign placeholder hero images to articles missing them'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Replace existing hero images',
        )

    def handle(self, *args, **options):
        force = options['force']
        articles = Article.objects.all().order_by('pk')
        updated = 0

        for i, article in enumerate(articles):
            if assign_hero_image(article, index=i, force=force):
                updated += 1
                self.stdout.write(f'  + {article.title}')

        self.stdout.write(self.style.SUCCESS(f'Done. Updated {updated} article(s).'))
