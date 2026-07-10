"""Generate placeholder hero images for articles."""
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont


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


def _wrap_title(title: str, max_chars: int = 28) -> list[str]:
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
    return lines[:3]


def generate_placeholder_image(title: str, category: str = '', index: int = 0) -> BytesIO:
    """Create a high-resolution JPEG placeholder with title and category overlay."""
    width, height = 1400, 788
    top_color, bottom_color = GRADIENTS[index % len(GRADIENTS)]

    img = Image.new('RGB', (width, height), top_color)
    draw = ImageDraw.Draw(img)

    # Vertical gradient
    r1, g1, b1 = int(top_color[1:3], 16), int(top_color[3:5], 16), int(top_color[5:7], 16)
    r2, g2, b2 = int(bottom_color[1:3], 16), int(bottom_color[3:5], 16), int(bottom_color[5:7], 16)
    for y in range(height):
        ratio = y / height
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Accent bar
    draw.rectangle([(0, 0), (width, 6)], fill='#FFB400')

    # Dark overlay for text area
    draw.rectangle([(0, height - 200), (width, height)], fill=(10, 25, 45))

    try:
        font_large = ImageFont.truetype('arial.ttf', 48)
        font_small = ImageFont.truetype('arial.ttf', 24)
    except OSError:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Category label
    if category:
        draw.text((40, height - 185), category.upper(), fill='#FFB400', font=font_small)

    # Title lines
    lines = _wrap_title(title)
    y_offset = height - 150
    for line in lines:
        draw.text((40, y_offset), line, fill='white', font=font_large)
        y_offset += 38

    # Watermark
    draw.text((40, 30), 'NextGen News', fill=(255, 255, 255, 180), font=font_small)

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
