"""Generate high-resolution placeholder hero images for articles."""
from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont


# Brand-aligned gradient pairs (top, bottom)
GRADIENTS = [
    ('#003366', '#0055A5'),
    ('#1a3a5c', '#2e6da4'),
    ('#0d2137', '#004080'),
    ('#1e4620', '#2d7a3e'),
    ('#4a235a', '#7d3c98'),
    ('#7b241c', '#c0392b'),
    ('#1a5276', '#3498db'),
    ('#784212', '#d68910'),
    ('#117a65', '#1abc9c'),
    ('#212f3d', '#566573'),
    ('#641e16', '#e74c3c'),
    ('#154360', '#5dade2'),
]

HERO_WIDTH = 1920
HERO_HEIGHT = 1080

_FONT_CANDIDATES = [
    Path('C:/Windows/Fonts/arialbd.ttf'),
    Path('C:/Windows/Fonts/arial.ttf'),
    Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),
    Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),
    Path('/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'),
    Path('/Library/Fonts/Arial Bold.ttf'),
    Path('/Library/Fonts/Arial.ttf'),
]


def _load_font(size: int) -> ImageFont.ImageFont:
    for path in _FONT_CANDIDATES:
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except OSError:
                continue
    return ImageFont.load_default()


def _wrap_title(title: str, max_chars: int = 34) -> list[str]:
    words = title.split()
    lines: list[str] = []
    current: list[str] = []
    length = 0
    for word in words:
        if length + len(word) + 1 > max_chars and current:
            lines.append(' '.join(current))
            current = [word]
            length = len(word)
        else:
            current.append(word)
            length += len(word) + 1
    if current:
        lines.append(' '.join(current))
    return lines[:4]


def generate_placeholder_image(title: str, category: str = '', index: int = 0) -> BytesIO:
    """Create a sharp 1920x1080 JPEG placeholder with title and category overlay."""
    width, height = HERO_WIDTH, HERO_HEIGHT
    top_color, bottom_color = GRADIENTS[index % len(GRADIENTS)]

    img = Image.new('RGB', (width, height), top_color)
    draw = ImageDraw.Draw(img)

    r1, g1, b1 = int(top_color[1:3], 16), int(top_color[3:5], 16), int(top_color[5:7], 16)
    r2, g2, b2 = int(bottom_color[1:3], 16), int(bottom_color[3:5], 16), int(bottom_color[5:7], 16)
    for y in range(height):
        ratio = y / height
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Soft light bloom for depth
    bloom = Image.new('RGB', (width, height), (255, 255, 255))
    bloom_mask = Image.new('L', (width, height), 0)
    bloom_draw = ImageDraw.Draw(bloom_mask)
    bloom_draw.ellipse([width // 3, -height // 4, width + 80, height // 2], fill=55)
    img = Image.composite(bloom, img, bloom_mask)
    draw = ImageDraw.Draw(img)

    draw.rectangle([(0, 0), (width, 10)], fill='#FFB400')
    draw.rectangle([(0, height - 280), (width, height)], fill=(8, 18, 34))

    font_large = _load_font(64)
    font_small = _load_font(28)
    font_brand = _load_font(26)

    if category:
        draw.text((56, height - 250), category.upper(), fill='#FFB400', font=font_small)

    lines = _wrap_title(title)
    y_offset = height - 200
    for line in lines:
        draw.text((56, y_offset), line, fill='white', font=font_large)
        y_offset += 72

    draw.text((56, 42), 'NextGen News', fill=(255, 255, 255), font=font_brand)

    img = img.filter(ImageFilter.UnsharpMask(radius=1.4, percent=120, threshold=2))
    img = ImageEnhance.Contrast(img).enhance(1.06)

    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=95, optimize=True, progressive=True)
    buffer.seek(0)
    return buffer


def assign_hero_image(article, index: int = 0, force: bool = False) -> bool:
    """Save a generated placeholder as the article hero image."""
    if article.hero_image and not force:
        return False

    category_name = article.category.name if article.category else 'News'
    buffer = generate_placeholder_image(article.title, category_name, index)
    filename = f'{article.slug}.jpg'
    article.hero_image.save(filename, ContentFile(buffer.read()), save=True)
    if not article.hero_image_caption:
        article.hero_image_caption = f'Illustration for {article.title}'
        article.save(update_fields=['hero_image_caption'])
    return True
