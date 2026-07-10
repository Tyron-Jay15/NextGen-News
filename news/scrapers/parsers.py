"""HTML parsing helpers for scraped content."""
import re
from html import unescape

from bs4 import BeautifulSoup


BBC_BODY_SELECTORS = [
    '[data-component="text-block"]',
    '[data-component="subheadline-block"]',
    'article[data-testid="article-body"]',
    '.article__body',
    '.story-body',
    'article',
    '[role="article"]',
    '.entry-content',
    'main',
]

GENERIC_BODY_SELECTORS = [
    'article',
    '[role="article"]',
    '.article-body',
    '.story-body',
    '.entry-content',
    'main',
]


def normalize_text(text: str) -> str:
    """Clean whitespace and common mojibake from scraped text."""
    if not text:
        return ''
    text = text.replace('\xa0', ' ')
    text = text.replace('\ufffd', '')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def clean_html(html: str) -> str:
    """Strip scripts/styles and return readable paragraph HTML."""
    if not html:
        return ''

    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(['script', 'style', 'iframe', 'noscript', 'nav', 'footer', 'header', 'aside']):
        tag.decompose()

    text_parts = []
    for element in soup.find_all(['p', 'h2', 'h3', 'li', 'blockquote']):
        text = normalize_text(element.get_text(separator=' ', strip=True))
        if len(text) >= 40:
            text_parts.append(f'<p>{unescape(text)}</p>')

    if text_parts:
        return '\n'.join(text_parts[:12])

    plain = normalize_text(soup.get_text(separator=' ', strip=True))
    if len(plain) >= 80:
        sentences = re.split(r'(?<=[.!?])\s+', plain)
        paragraphs = []
        chunk = []
        for sentence in sentences:
            chunk.append(sentence)
            if len(' '.join(chunk)) >= 180:
                paragraphs.append(f'<p>{unescape(" ".join(chunk))}</p>')
                chunk = []
        if chunk:
            paragraphs.append(f'<p>{unescape(" ".join(chunk))}</p>')
        return '\n'.join(paragraphs[:8])

    return f'<p>{unescape(plain)}</p>' if plain else ''


def extract_article_body(html: str, url: str = '') -> str:
    """Extract main article content from a full HTML page."""
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'form']):
        tag.decompose()

    selectors = BBC_BODY_SELECTORS if 'bbc.co.uk' in url or 'bbc.com' in url else GENERIC_BODY_SELECTORS
    for selector in selectors:
        if selector in ('article', 'main', '[role="article"]'):
            node = soup.select_one(selector)
        else:
            nodes = soup.select(selector)
            if nodes and selector.startswith('[data-component'):
                parts = []
                for node in nodes:
                    part = clean_html(str(node))
                    if part:
                        parts.append(part)
                if parts:
                    body = '\n'.join(parts)
                    if len(BeautifulSoup(body, 'html.parser').get_text(strip=True)) >= 120:
                        return body
                continue
            node = soup.select_one(selector)

        if node:
            body = clean_html(str(node))
            if len(BeautifulSoup(body, 'html.parser').get_text(strip=True)) >= 120:
                return body

    return clean_html(str(soup.body or soup))


def extract_og_image(html: str) -> str | None:
    """Get Open Graph image URL from page HTML."""
    soup = BeautifulSoup(html, 'html.parser')
    og = soup.find('meta', property='og:image')
    if og and og.get('content'):
        return og['content']
    twitter = soup.find('meta', attrs={'name': 'twitter:image'})
    if twitter and twitter.get('content'):
        return twitter['content']
    return None


def _best_srcset_url(srcset: str) -> str | None:
    """Pick the widest image URL from a srcset attribute."""
    best_url = None
    best_width = 0
    for part in srcset.split(','):
        part = part.strip()
        if not part:
            continue
        pieces = part.split()
        if not pieces:
            continue
        url = pieces[0]
        width = 0
        if len(pieces) > 1 and pieces[1].endswith('w'):
            try:
                width = int(pieces[1][:-1])
            except ValueError:
                width = 0
        if width >= best_width:
            best_width = width
            best_url = url
    return best_url


def extract_article_image(html: str, page_url: str = '') -> str | None:
    """Find the best lead image URL from article HTML (OG tag or in-page images)."""
    from news.utils.images import upgrade_image_url

    candidates: list[str] = []
    og = extract_og_image(html)
    if og:
        candidates.append(og)

    soup = BeautifulSoup(html, 'html.parser')
    selectors = (
        'article img',
        '[data-component="image-block"] img',
        'figure img',
        '.article__media img',
    )
    for selector in selectors:
        for img in soup.select(selector):
            srcset = img.get('srcset', '')
            if srcset:
                best = _best_srcset_url(srcset)
                if best:
                    candidates.append(best)
            src = img.get('src') or img.get('data-src')
            if src and src.startswith('http'):
                candidates.append(src)

    if not candidates:
        return None

    def score(url: str) -> int:
        upgraded = upgrade_image_url(url)
        for text in (upgraded, url):
            match = re.search(r'/(?:standard|branded_news|news)/(\d+)/', text)
            if match:
                return int(match.group(1))
        return 100

    best = max(candidates, key=score)
    return upgrade_image_url(best)


def is_google_news_url(url: str) -> bool:
    return bool(url and 'news.google.com' in url)


def split_google_news_title(title: str) -> tuple[str, str]:
    """Split 'Headline - Publisher' titles from Google News."""
    if ' - ' in title:
        headline, publisher = title.rsplit(' - ', 1)
        return headline.strip(), publisher.strip()
    return title.strip(), ''


def build_summary_body(title: str, excerpt: str = '', publisher: str = '') -> str:
    """Readable fallback when full article text cannot be fetched."""
    headline, source = split_google_news_title(title)
    if not source and publisher:
        source = publisher
    lead = normalize_text(excerpt) or headline
    parts = [f'<p>{unescape(lead)}</p>']
    if source:
        parts.append(f'<p><em>Source: {unescape(source)}</em></p>')
    return '\n'.join(parts)
