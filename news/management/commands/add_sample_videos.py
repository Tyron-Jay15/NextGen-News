"""Attach verified YouTube videos to demo articles."""
from django.core.management.base import BaseCommand

from news.models import Article
from news.utils.video import validate_video_url

# Real, embeddable YouTube videos matched to article topics
SAMPLE_VIDEOS = {
    'ai-revolution-transforms-healthcare-industry': 'https://www.youtube.com/watch?v=aircAruvnKk',
    'national-team-secures-victory-in-championship': 'https://www.youtube.com/watch?v=pRpeEdMmmQ0',
    'blockbuster-film-breaks-box-office-records': 'https://www.youtube.com/watch?v=8ugaeA-nMTc',
    'global-summit-addresses-climate-change': 'https://www.youtube.com/watch?v=LwRTw_7NNJs',
}


class Command(BaseCommand):
    help = 'Add verified YouTube videos to existing articles'

    def handle(self, *args, **options):
        updated = 0
        for slug, url in SAMPLE_VIDEOS.items():
            if not validate_video_url(url):
                self.stdout.write(self.style.WARNING(f'  Skipped invalid video URL for {slug}'))
                continue
            count = Article.objects.filter(slug=slug).update(video_url=url)
            updated += count
            if count:
                self.stdout.write(f'  Video added: {slug}')

        self.stdout.write(self.style.SUCCESS(f'Updated {updated} article(s) with sample videos.'))
