"""Credibility and fake-news screening for scraped articles."""
import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from config.utils import generate_content_hash
from news.models import Article


TRUSTED_PUBLISHER_DOMAINS = (
    'bbc.co.uk',
    'bbc.com',
    'panaynews.net',
    'reuters.com',
    'apnews.com',
    'pbs.org',
    'npr.org',
)

SUSPICIOUS_HEADLINE_PATTERNS = (
    r"you won'?t believe",
    r'shocking truth',
    r'doctors hate',
    r'click here',
    r'free money',
    r'100% guaranteed',
    r'conspiracy',
    r'hoax exposed',
    r'fake news',
)

DEMO_CONTENT_MARKERS = (
    'lorem ipsum',
    'dolor sit amet',
    'consectetur adipiscing',
)

MIN_BODY_CHARS = 200
MIN_CREDIBILITY_SCORE = 70.0


@dataclass
class VerificationResult:
    is_legitimate: bool
    score: float
    reasons: list[str] = field(default_factory=list)


class CredibilityScanner:
    """Rule-based legitimacy scan before scraped articles go live."""

    @classmethod
    def scan(
        cls,
        *,
        title: str,
        body_html: str,
        external_url: str,
        source_name: str = '',
    ) -> VerificationResult:
        reasons: list[str] = []
        score = 100.0
        plain = cls._plain_text(body_html)
        title = (title or '').strip()

        if not title or len(title) < 12:
            score -= 40
            reasons.append('Headline is missing or too short.')

        if len(plain) < MIN_BODY_CHARS:
            score -= 35
            reasons.append('Article body is too short to verify as full news.')

        lowered = plain.lower()
        if any(marker in lowered for marker in DEMO_CONTENT_MARKERS):
            score = 0.0
            reasons.append('Demo or placeholder content detected.')

        domain = cls._domain(external_url)
        if not domain or not cls._is_trusted_domain(domain):
            score -= 50
            reasons.append(f'Publisher domain is not on the trusted list ({domain or "unknown"}).')

        if source_name and 'google news' in source_name.lower():
            score -= 60
            reasons.append('Google News redirect sources are not allowed for auto-publish.')

        for pattern in SUSPICIOUS_HEADLINE_PATTERNS:
            if re.search(pattern, title, re.IGNORECASE):
                score -= 30
                reasons.append('Headline matched a suspicious clickbait pattern.')
                break

        content_hash = generate_content_hash(plain)
        if content_hash and Article.objects.filter(
            duplicate_hash=content_hash,
            status='published',
            verification_status='verified',
        ).exists():
            score = 0.0
            reasons.append('Duplicate story already published.')

        score = max(0.0, min(100.0, score))
        is_legitimate = score >= MIN_CREDIBILITY_SCORE and score > 0
        if is_legitimate and not reasons:
            reasons.append('Passed trusted-source and content-quality checks.')

        return VerificationResult(is_legitimate=is_legitimate, score=score, reasons=reasons)

    @staticmethod
    def _plain_text(html: str) -> str:
        if not html:
            return ''
        text = BeautifulSoup(html, 'html.parser').get_text(separator=' ', strip=True)
        return re.sub(r'\s+', ' ', text).strip()

    @staticmethod
    def _domain(url: str) -> str:
        if not url:
            return ''
        host = urlparse(url).netloc.lower()
        return host[4:] if host.startswith('www.') else host

    @classmethod
    def _is_trusted_domain(cls, domain: str) -> bool:
        return any(domain == trusted or domain.endswith('.' + trusted) for trusted in TRUSTED_PUBLISHER_DOMAINS)
