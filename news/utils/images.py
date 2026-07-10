"""Image optimization utilities for article hero images."""
import re
from io import BytesIO

from PIL import Image, ImageEnhance, ImageFilter


MIN_HERO_WIDTH = 900
TARGET_WIDTH = 1400
TARGET_HEIGHT = 788  # 16:9


def upgrade_image_url(url: str) -> str:
    """Request a higher-resolution variant when the URL supports it."""
    if not url:
        return url

    # Google News / Google CDN thumbnails
    if 'googleusercontent.com' in url or 'ggpht.com' in url:
        url = re.sub(r'=s\d+(-w\d+-rw)?', '=s1400-rw', url)
        url = re.sub(r'=w\d+-h\d+', '=w1400-h788', url)

    # BBC image CDN — request the largest standard rendition
    if 'ichef.bbci.co.uk' in url:
        url = re.sub(r'/standard/\d+/', '/standard/1920/', url)
        url = re.sub(r'/branded_news/\d+/', '/branded_news/1600/', url)
        url = re.sub(r'/news/\d+/', '/news/976/', url)

    # Legacy BBC path segments
    url = url.replace('/320/', '/976/').replace('/480/', '/976/').replace('/640/', '/976/')

    # WordPress-style resized images
    url = re.sub(r'-\d+x\d+\.(jpg|jpeg|png|webp)', r'.\1', url, flags=re.IGNORECASE)

    # Generic width/height query params
    url = re.sub(r'([?&]w=)\d+', r'\g<1>1400', url)
    url = re.sub(r'([?&]h=)\d+', r'\g<1>788', url)

    return url


def optimize_image_bytes(content: bytes, min_width: int = MIN_HERO_WIDTH) -> bytes | None:
    """
    Normalize and enhance downloaded image bytes.
    Returns None if the image is too small to use as a hero image.
    """
    try:
        img = Image.open(BytesIO(content))
    except Exception:
        return None

    if img.mode in ('RGBA', 'P', 'LA'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    if img.width < min_width:
        return None

    # Downscale large images with high-quality filter (never upscale)
    if img.width > TARGET_WIDTH or img.height > TARGET_HEIGHT:
        img.thumbnail((TARGET_WIDTH, TARGET_HEIGHT), Image.Resampling.LANCZOS)

    # Light sharpen for web display clarity
    img = img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=110, threshold=3))
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.05)

    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=92, optimize=True, progressive=True)
    buffer.seek(0)
    return buffer.read()
