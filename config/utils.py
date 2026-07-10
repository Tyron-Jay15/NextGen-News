"""Shared utility functions."""
import hashlib
import re
from typing import Optional

from django.http import HttpRequest


def get_client_ip(request: HttpRequest) -> str:
    """Extract client IP from request."""
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def estimate_reading_time(text: str, wpm: int = 200) -> int:
    """Estimate reading time in minutes."""
    word_count = len(re.findall(r'\w+', text))
    return max(1, round(word_count / wpm))


def generate_content_hash(text: str) -> str:
    """Generate hash for duplicate detection."""
    normalized = re.sub(r'\s+', ' ', text.lower().strip())
    return hashlib.sha256(normalized.encode()).hexdigest()


def truncate_words(text: str, count: int = 30) -> str:
    """Truncate text to word count."""
    words = text.split()
    if len(words) <= count:
        return text
    return ' '.join(words[:count]) + '...'


def detect_device_type(user_agent: str) -> str:
    """Detect device type from user agent."""
    ua = user_agent.lower()
    if any(m in ua for m in ('mobile', 'android', 'iphone')):
        return 'mobile'
    if any(t in ua for t in ('ipad', 'tablet')):
        return 'tablet'
    return 'desktop'
