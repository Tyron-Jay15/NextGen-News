"""Parse and embed YouTube / Vimeo URLs."""
import re
from dataclasses import dataclass
from urllib.parse import quote


@dataclass
class VideoInfo:
    provider: str
    video_id: str
    embed_url: str
    watch_url: str
    thumbnail_url: str | None = None


YOUTUBE_PATTERNS = (
    r'(?:youtube\.com/watch\?.*v=|youtu\.be/|youtube\.com/embed/|youtube-nocookie\.com/embed/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})',
)
VIMEO_PATTERN = r'vimeo\.com/(?:video/)?(\d+)'


def parse_video_url(url: str) -> VideoInfo | None:
    """Return embed metadata for a supported video URL."""
    if not url:
        return None

    url = url.strip()
    for pattern in YOUTUBE_PATTERNS:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            return VideoInfo(
                provider='youtube',
                video_id=video_id,
                embed_url=(
                    f'https://www.youtube-nocookie.com/embed/{video_id}'
                    f'?rel=0&modestbranding=1&playsinline=1'
                ),
                watch_url=f'https://www.youtube.com/watch?v={video_id}',
                thumbnail_url=f'https://img.youtube.com/vi/{video_id}/hqdefault.jpg',
            )

    match = re.search(VIMEO_PATTERN, url)
    if match:
        video_id = match.group(1)
        return VideoInfo(
            provider='vimeo',
            video_id=video_id,
            embed_url=f'https://player.vimeo.com/video/{video_id}',
            watch_url=f'https://vimeo.com/{video_id}',
        )

    return None


def validate_video_url(url: str) -> bool:
    """Check that a video URL resolves via the provider oEmbed API."""
    info = parse_video_url(url)
    if not info:
        return False

    if info.provider == 'youtube':
        import json
        import urllib.error
        import urllib.request

        oembed = (
            'https://www.youtube.com/oembed?format=json&url='
            + quote(info.watch_url, safe='')
        )
        try:
            with urllib.request.urlopen(oembed, timeout=10) as response:
                json.loads(response.read())
            return True
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError):
            return False

    return True
