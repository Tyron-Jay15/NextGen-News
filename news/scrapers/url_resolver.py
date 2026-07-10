"""Resolve scraped article URLs to publisher pages."""
from urllib.parse import urlparse

from news.scrapers.parsers import is_google_news_url


def resolve_article_url(url: str) -> str | None:
    """
    Return a publisher URL suitable for full-text fetching.
    Google News RSS links cannot be scraped reliably, so they are skipped.
    """
    if not url:
        return None
    if is_google_news_url(url):
        return None

    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https') or not parsed.netloc:
        return None

    return url
