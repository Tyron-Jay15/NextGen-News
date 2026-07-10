"""Celery tasks for news scraping."""
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name='news.scrape_all_sources')
def scrape_all_news_sources():
    """Fetch all active news sources and post new articles."""
    from news.scrapers.service import NewsScraperService
    result = NewsScraperService.scrape_all()
    logger.info('News scrape finished: %s', result)
    return result


@shared_task(name='news.scrape_source')
def scrape_single_source(source_id: int):
    """Scrape one news source by ID."""
    from news.models import NewsSource
    from news.scrapers.service import NewsScraperService

    try:
        source = NewsSource.objects.get(pk=source_id, is_active=True)
    except NewsSource.DoesNotExist:
        return {'error': 'Source not found'}
    return NewsScraperService.scrape_source(source)
