"""Template tags for video embeds."""
from django import template

from news.utils.video import parse_video_url

register = template.Library()


@register.inclusion_tag('partials/video_embed.html')
def video_embed(url, caption='', css_class=''):
    return {
        'info': parse_video_url(url) if url else None,
        'caption': caption,
        'css_class': css_class,
    }


@register.filter
def video_info(url):
    return parse_video_url(url) if url else None
