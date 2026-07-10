"""Prepare the site for hosting with verified RSS news only."""
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from news.models import Article, NewsSource
from news.scrapers.service import NewsScraperService
from news.scrapers.verification import CredibilityScanner


class Command(BaseCommand):
    help = 'Remove demo articles, configure BBC RSS sources, verify existing news, and scrape fresh stories'

    def add_arguments(self, parser):
        parser.add_argument('--skip-scrape', action='store_true', help='Do not fetch new RSS items')

    def handle(self, *args, **options):
        self.stdout.write('Preparing live news site...')

        call_command('remove_demo_articles')
        call_command('setup_scraper_sources')

        NewsSource.objects.filter(name__icontains='Google News').update(is_active=False, is_trusted=False)
        NewsSource.objects.filter(name__icontains='BBC').update(is_active=True, is_trusted=True, fetch_full_content=True)

        verified = 0
        archived = 0
        for article in Article.objects.filter(is_scraped=True, status='published'):
            body_only = NewsScraperService._strip_attribution_footer(article.body)
            result = CredibilityScanner.scan(
                title=article.title,
                body_html=body_only,
                external_url=article.external_url or article.canonical_url,
                source_name=article.news_source.name if article.news_source else '',
            )
            article.ai_score = result.score
            article.verification_notes = '\n'.join(result.reasons)
            if result.is_legitimate:
                article.verification_status = 'verified'
                article.verified_at = article.verified_at or timezone.now()
                article.save(update_fields=[
                    'ai_score', 'verification_status', 'verification_notes', 'verified_at',
                ])
                verified += 1
            else:
                article.status = 'archived'
                article.verification_status = 'rejected'
                article.archived_at = timezone.now()
                article.save(update_fields=[
                    'status', 'ai_score', 'verification_status', 'verification_notes', 'archived_at',
                ])
                archived += 1

        self.stdout.write(f'Verified {verified} existing scraped article(s); archived {archived} failed scan(s).')

        Article.objects.filter(is_scraped=True, external_url__icontains='news.google.com').update(
            status='archived',
            verification_status='rejected',
        )

        if not options['skip_scrape']:
            totals = NewsScraperService.scrape_all()
            self.stdout.write(
                f"Scrape complete: {totals['created']} new verified, "
                f"{totals['rejected']} rejected by scanner, {totals['skipped']} skipped."
            )

        published = Article.objects.filter(is_scraped=True, status='published', verification_status='verified').count()
        self.stdout.write(self.style.SUCCESS(
            f'Ready to host. {published} verified RSS article(s) are live on the public site.'
        ))
