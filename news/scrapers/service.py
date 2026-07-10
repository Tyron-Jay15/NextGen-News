"""Automated news scraping service."""
import calendar
import hashlib
import logging
from datetime import datetime, timezone as dt_timezone
from typing import Any
from urllib.parse import urlparse

import feedparser
import requests
from bs4 import BeautifulSoup
from django.core.files.base import ContentFile
from django.utils import timezone
from django.utils.text import slugify

from news.models import Article, NewsSource, ScrapedItemLog
from news.scrapers.parsers import (
    build_summary_body, clean_html, extract_article_body, extract_article_image, is_google_news_url,
)
from news.scrapers.sucuri import fetch_with_sucuri_bypass, is_sucuri_challenge
from news.scrapers.url_resolver import resolve_article_url
from news.scrapers.verification import CredibilityScanner
from news.services import ArticleService
from news.utils.images import optimize_image_bytes, upgrade_image_url
from news.utils.placeholders import assign_hero_image

logger = logging.getLogger(__name__)

REQUEST_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}
REQUEST_TIMEOUT = 20

# Sites protected by JS/cookie challenges — use RSS summary text instead of page scrape
RSS_SUMMARY_DOMAINS = ('panaynews.net',)


class NewsScraperService:
    """Fetch RSS feeds and post new articles to the portal."""

    @classmethod
    def scrape_all(cls) -> dict[str, int]:
        totals = {'sources': 0, 'created': 0, 'skipped': 0, 'rejected': 0, 'errors': 0}
        for source in NewsSource.objects.filter(is_active=True):
            totals['sources'] += 1
            result = cls.scrape_source(source)
            totals['created'] += result['created']
            totals['skipped'] += result['skipped']
            totals['rejected'] += result.get('rejected', 0)
            totals['errors'] += result['errors']
        return totals

    @classmethod
    def scrape_source(cls, source: NewsSource) -> dict[str, int]:
        result = {'created': 0, 'skipped': 0, 'rejected': 0, 'errors': 0}
        try:
            if not source.is_trusted:
                logger.warning('Skipping untrusted source: %s', source.name)
                return result
            if source.source_type == 'rss':
                entries = cls._fetch_rss_entries(source.feed_url)
            else:
                entries = cls._fetch_html_entries(source.feed_url)

            for entry in entries:
                try:
                    outcome = cls._process_entry(source, entry)
                    if outcome == 'created':
                        result['created'] += 1
                    elif outcome == 'rejected':
                        result['rejected'] += 1
                    else:
                        result['skipped'] += 1
                except Exception:
                    logger.exception('Failed to process entry from %s', source.name)
                    result['errors'] += 1

            source.last_fetched_at = timezone.now()
            source.last_error = ''
            source.save(update_fields=['last_fetched_at', 'last_error'])
        except Exception as exc:
            logger.exception('Failed to scrape source %s', source.name)
            source.last_error = str(exc)[:500]
            source.save(update_fields=['last_error'])
            result['errors'] += 1
        return result

    @classmethod
    def _fetch_rss_entries(cls, feed_url: str) -> list[dict[str, Any]]:
        response = requests.get(feed_url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        feed = feedparser.parse(response.content)
        entries = []
        for item in feed.entries[:10]:
            guid = item.get('id') or item.get('link') or item.get('title', '')
            if not guid:
                continue
            published = None
            if item.get('published_parsed'):
                published = datetime.fromtimestamp(
                    calendar.timegm(item.published_parsed), tz=dt_timezone.utc
                )
            elif item.get('updated_parsed'):
                published = datetime.fromtimestamp(
                    calendar.timegm(item.updated_parsed), tz=dt_timezone.utc
                )

            image_url = cls._extract_rss_image(item)
            entries.append({
                'guid': guid,
                'title': item.get('title', 'Untitled').strip(),
                'link': item.get('link', ''),
                'summary': item.get('summary', item.get('description', '')),
                'published': published,
                'image_url': image_url,
            })
        return entries

    @staticmethod
    def _extract_rss_image(item) -> str | None:
        if item.get('media_content'):
            for media in item.media_content:
                if media.get('url'):
                    return media['url']
        if item.get('media_thumbnail'):
            for thumb in item.media_thumbnail:
                if thumb.get('url'):
                    return thumb['url']
        for link in item.get('links', []):
            if link.get('type', '').startswith('image') and link.get('href'):
                return link['href']
        return None

    @classmethod
    def _fetch_html_entries(cls, page_url: str) -> list[dict[str, Any]]:
        """Scrape article links from a listing page."""
        response = requests.get(page_url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        base = f'{urlparse(page_url).scheme}://{urlparse(page_url).netloc}'
        entries = []
        seen = set()
        for anchor in soup.find_all('a', href=True):
            href = anchor['href']
            title = anchor.get_text(strip=True)
            if not title or len(title) < 20:
                continue
            if href.startswith('/'):
                href = base + href
            if not href.startswith('http'):
                continue
            if href in seen:
                continue
            seen.add(href)
            entries.append({
                'guid': href,
                'title': title[:300],
                'link': href,
                'summary': '',
                'published': timezone.now(),
                'image_url': None,
            })
            if len(entries) >= 15:
                break
        return entries

    @classmethod
    def _process_entry(cls, source: NewsSource, entry: dict[str, Any]) -> str:
        """Return 'created', 'rejected', or 'skipped'."""
        guid = entry['guid']
        if ScrapedItemLog.objects.filter(external_guid=guid).exists():
            return 'skipped'
        if Article.objects.filter(external_guid=guid).exists():
            return 'skipped'

        title = entry['title'][:300]
        link = entry.get('link', '')
        publisher_url = resolve_article_url(link)

        if is_google_news_url(link):
            logger.info('Skipping Google News redirect (no full article text): %s', title)
            return 'skipped'

        body_html = ''
        og_image = None
        if publisher_url and cls._uses_rss_summary_only(publisher_url):
            body_html = clean_html(entry.get('summary', ''))
            logger.debug('Using RSS summary for %s (publisher blocks automated fetch)', title)
            page_html = cls._fetch_page_html(publisher_url)
            og_image = extract_article_image(page_html, publisher_url) if page_html else None
        elif publisher_url:
            full_body, page_html = cls._fetch_full_article(publisher_url)
            if full_body and not cls._is_blocked_page(full_body):
                body_html = full_body
            og_image = extract_article_image(page_html, publisher_url) if page_html else None
            if not body_html:
                body_html = clean_html(entry.get('summary', ''))

        text_len = len(BeautifulSoup(body_html, 'html.parser').get_text(strip=True))
        if text_len < 120:
            body_html = build_summary_body(title, entry.get('summary', ''))
            text_len = len(BeautifulSoup(body_html, 'html.parser').get_text(strip=True))

        if text_len < 120:
            logger.info('Insufficient article text, skipping: %s', title)
            return 'skipped'

        verification = CredibilityScanner.scan(
            title=title,
            body_html=body_html,
            external_url=read_link if (read_link := publisher_url or link) else '',
            source_name=source.name,
        )
        if not verification.is_legitimate:
            logger.warning(
                'Credibility scan rejected "%s" from %s (score=%.0f): %s',
                title,
                source.name,
                verification.score,
                '; '.join(verification.reasons),
            )
            return 'rejected'

        if og_image:
            entry['image_url'] = og_image
        elif not entry.get('image_url'):
            entry['image_url'] = None

        attribution = source.attribution_name or source.name
        footer = (
            f'<hr><p><em>This article was sourced from '
            f'<a href="{read_link}" target="_blank" rel="noopener noreferrer">{attribution}</a>. '
            f'<a href="{read_link}" target="_blank" rel="noopener noreferrer">Read the full story on {attribution}</a>.</em></p>'
        )
        body = (body_html or f'<p>{title}</p>') + footer

        summary_raw = entry.get('summary', '')
        excerpt_text = BeautifulSoup(body_html, 'html.parser').get_text(separator=' ', strip=True)[:400]
        if not excerpt_text:
            excerpt_text = BeautifulSoup(summary_raw, 'html.parser').get_text(separator=' ', strip=True)[:400]

        status = 'published' if source.auto_publish else 'draft'
        published_at = entry.get('published') or timezone.now()
        if status == 'published' and published_at > timezone.now():
            published_at = timezone.now()

        now = timezone.now()
        article = Article(
            title=title,
            slug=cls._unique_slug(title),
            excerpt=excerpt_text or title[:400],
            body=body,
            category=source.category,
            status=status,
            is_scraped=True,
            external_url=read_link,
            external_guid=guid,
            news_source=source,
            published_at=published_at if status == 'published' else None,
            canonical_url=read_link,
            allow_comments=True,
            province=cls._source_province(source),
            ai_score=verification.score,
            verification_status='verified' if verification.is_legitimate else 'rejected',
            verification_notes='\n'.join(verification.reasons),
            verified_at=now if verification.is_legitimate else None,
        )
        ArticleService.prepare_article(article)
        article.save()

        if entry.get('image_url'):
            cls._download_hero_image(
                article,
                entry['image_url'],
                credit=attribution,
                publisher_url=read_link,
            )
        else:
            assign_hero_image(article, index=source.pk)

        ScrapedItemLog.objects.create(
            source=source,
            external_guid=guid,
            external_url=read_link,
            article=article,
        )
        source.articles_fetched += 1
        source.save(update_fields=['articles_fetched'])
        logger.info('Scraped verified article: %s from %s (score=%.0f)', title, source.name, verification.score)
        return 'created'

    @classmethod
    def refresh_article_body(cls, article: Article) -> bool:
        """Re-fetch full article text for an existing scraped article."""
        url = resolve_article_url(article.external_url or article.canonical_url)
        if not url:
            return False

        full_body, _ = cls._fetch_full_article(url)
        if not full_body:
            return False

        attribution = article.news_source.attribution_name if article.news_source else 'Original source'
        footer = (
            f'<hr><p><em>This article was sourced from '
            f'<a href="{url}" target="_blank" rel="noopener noreferrer">{attribution}</a>. '
            f'<a href="{url}" target="_blank" rel="noopener noreferrer">Read the full story</a>.</em></p>'
        )
        article.body = full_body + footer
        article.canonical_url = url
        article.external_url = url
        plain = BeautifulSoup(full_body, 'html.parser').get_text(separator=' ', strip=True)
        if plain:
            article.excerpt = plain[:400]
        article.save(update_fields=['body', 'canonical_url', 'external_url', 'excerpt'])
        return True

    @staticmethod
    def _strip_attribution_footer(body: str) -> str:
        if '<hr>' in body:
            return body.split('<hr>', 1)[0].strip()
        return body

    @classmethod
    def refresh_hero_image(cls, article: Article) -> bool:
        """Re-download a sharp hero image from the original publisher page."""
        page_url = resolve_article_url(article.external_url or article.canonical_url)
        if not page_url:
            return False

        page_html = cls._fetch_page_html(page_url)
        image_url = extract_article_image(page_html, page_url) if page_html else None
        if not image_url:
            return False

        credit = ''
        if article.news_source:
            credit = article.news_source.attribution_name or article.news_source.name

        old_name = article.hero_image.name if article.hero_image else ''
        cls._download_hero_image(article, image_url, credit=credit, publisher_url=page_url)
        article.refresh_from_db(fields=['hero_image', 'hero_image_caption'])
        if not article.hero_image:
            return False
        if article.hero_image.name == old_name and old_name.endswith('.jpg') and 'scraped-' not in old_name:
            return False
        return 'scraped-' in article.hero_image.name

    @classmethod
    def _fetch_page_html(cls, url: str) -> str:
        """Fetch raw HTML, bypassing Sucuri challenges on protected publishers."""
        try:
            session = requests.Session()
            if cls._uses_rss_summary_only(url):
                response = fetch_with_sucuri_bypass(
                    session,
                    url,
                    timeout=REQUEST_TIMEOUT,
                    headers=REQUEST_HEADERS,
                )
            else:
                response = session.get(url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            response.encoding = response.apparent_encoding or response.encoding or 'utf-8'
            if cls._is_blocked_page(response.text):
                return ''
            return response.text
        except Exception:
            logger.exception('Could not fetch page HTML from %s', url)
            return ''

    @classmethod
    def _fetch_full_article(cls, url: str) -> tuple[str, str]:
        try:
            html = cls._fetch_page_html(url)
            if not html:
                return '', ''
            return extract_article_body(html, url), html
        except Exception:
            logger.exception('Could not fetch full article from %s', url)
            return '', ''

    @classmethod
    def _download_hero_image(
        cls,
        article: Article,
        image_url: str,
        credit: str = '',
        publisher_url: str = '',
    ) -> None:
        upgraded_url = upgrade_image_url(image_url)
        min_width = 640 if publisher_url and ('bbc.co.uk' in publisher_url or 'panaynews.net' in publisher_url) else 900
        for url in dict.fromkeys([upgraded_url, image_url]):
            try:
                response = requests.get(url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                optimized = optimize_image_bytes(response.content, min_width=min_width)
                if optimized:
                    filename = f'scraped-{article.slug[:50]}.jpg'
                    article.hero_image.save(filename, ContentFile(optimized), save=True)
                    if credit and not article.hero_image_caption:
                        article.hero_image_caption = f'Image courtesy of {credit}'
                        article.save(update_fields=['hero_image_caption'])
                    return
            except Exception:
                logger.debug('Image download failed for %s', url)

        # Tiny or missing image — use sharp generated placeholder instead of pixelated upscale
        logger.info('Using placeholder for %s (source image too small or unavailable)', article.title)
        assign_hero_image(article, index=article.pk or 0, force=True)

    @staticmethod
    def _uses_rss_summary_only(url: str) -> bool:
        return any(domain in url for domain in RSS_SUMMARY_DOMAINS)

    @staticmethod
    def _is_blocked_page(body_html: str) -> bool:
        if is_sucuri_challenge(body_html):
            return True
        plain = BeautifulSoup(body_html, 'html.parser').get_text(strip=True).lower()
        return 'being redirected' in plain or len(plain) < 80

    @staticmethod
    def _source_province(source: NewsSource) -> str:
        name = source.name.lower()
        if 'iloilo' in name:
            return 'Iloilo'
        if 'negros' in name:
            return 'Negros Occidental'
        if 'nation' in name:
            return 'Philippines'
        if 'panay' in name:
            return 'Western Visayas'
        return ''

    @staticmethod
    def _unique_slug(title: str) -> str:
        base = slugify(title)[:280] or hashlib.md5(title.encode()).hexdigest()[:12]
        slug = base
        counter = 1
        while Article.objects.filter(slug=slug).exists():
            slug = f'{base}-{counter}'
            counter += 1
        return slug
