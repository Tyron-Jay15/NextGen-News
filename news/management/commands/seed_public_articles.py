"""Seed published sample articles for environments that cannot scrape RSS (e.g. free PA)."""
from datetime import timedelta

import requests
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from accounts.models import Role, User
from authors.models import AuthorProfile
from categories.models import Category, Tag
from news.models import Article
from news.services import ArticleService
from news.utils.images import optimize_image_bytes
from news.utils.placeholders import assign_hero_image


SAMPLE_ARTICLES = [
    {
        'title': 'Iloilo City expands riverside walkways to boost tourism and local trade',
        'category': 'Regional News',
        'province': 'Iloilo',
        'featured': True,
        'sticky': True,
        'breaking': False,
        'editors_pick': True,
        'image_seed': 'iloilo-river',
        'excerpt': (
            'City planners unveiled a multi-phase riverside project aimed at safer pedestrian '
            'access, greener public spaces, and stronger support for nearby small businesses.'
        ),
        'body': [
            'ILOILO CITY — Local officials formally launched an expanded riverside walkway '
            'program designed to improve mobility along the city’s waterfront districts.',
            'The plan includes wider pedestrian lanes, improved lighting, shaded rest areas, '
            'and clearer wayfinding for residents and visitors exploring nearby markets.',
            'Business groups welcomed the move, saying better foot traffic could help cafes, '
            'souvenir shops, and transport services around the Esplanade corridor.',
            'City engineers said construction will proceed in phases to limit disruption, with '
            'priority given to high-traffic stretches used by students and evening joggers.',
        ],
    },
    {
        'title': 'Western Visayas schools roll out digital literacy modules for senior high',
        'category': 'Education',
        'province': 'Western Visayas',
        'featured': True,
        'sticky': False,
        'breaking': False,
        'editors_pick': True,
        'image_seed': 'education-tech',
        'excerpt': (
            'Regional education offices introduced classroom modules on online safety, media '
            'literacy, and basic coding for senior high students across Western Visayas.'
        ),
        'body': [
            'Education supervisors across Western Visayas began distributing digital literacy '
            'modules intended to help senior high students navigate online information more carefully.',
            'Teachers received orientation sessions covering responsible social media use, '
            'spotting misleading content, and introductory computational thinking exercises.',
            'School heads said the materials are designed for both urban and rural campuses, '
            'including lessons that can run with limited internet connectivity.',
        ],
    },
    {
        'title': 'Negros farmers adopt climate-ready rice varieties ahead of wet season',
        'category': 'Business',
        'province': 'Negros Occidental',
        'featured': True,
        'sticky': False,
        'breaking': False,
        'editors_pick': False,
        'image_seed': 'rice-farm',
        'excerpt': (
            'Agricultural cooperatives in Negros Occidental are shifting to climate-ready rice '
            'strains as forecasts point to uneven rainfall through the coming planting months.'
        ),
        'body': [
            'BACOLOD CITY — Farmer cooperatives reported early adoption of climate-ready rice '
            'varieties recommended by regional agriculture offices.',
            'Extension workers said the seeds are better suited for periods of heavy rain and '
            'short dry spells that have become more common in recent seasons.',
            'Local traders expect stable supply if planting schedules stay on track, though '
            'transport costs remain a concern for inland municipalities.',
        ],
    },
    {
        'title': 'Global markets steady as tech earnings calm investor nerves',
        'category': 'International',
        'province': '',
        'featured': True,
        'sticky': False,
        'breaking': False,
        'editors_pick': False,
        'image_seed': 'global-markets',
        'excerpt': (
            'Major indexes held firm after leading technology firms posted stronger-than-expected '
            'results, easing fears of a sharper slowdown in global demand.'
        ),
        'body': [
            'International markets opened on a steadier note after a cluster of technology earnings '
            'reports reassured investors about corporate spending and cloud demand.',
            'Analysts said the rebound remains fragile, with attention now shifting to inflation '
            'data and central bank guidance in the weeks ahead.',
            'Currency traders also watched Asian markets for signals on export outlook and '
            'commodity prices tied to manufacturing activity.',
        ],
    },
    {
        'title': 'Health centers push free hypertension screening in barangay clinics',
        'category': 'Health',
        'province': 'Iloilo',
        'featured': False,
        'sticky': False,
        'breaking': True,
        'editors_pick': False,
        'image_seed': 'health-clinic',
        'excerpt': (
            'Municipal health offices launched weekend hypertension screening in barangay clinics '
            'to catch high blood pressure cases earlier among older residents.'
        ),
        'body': [
            'Barangay health workers began offering free blood-pressure checks and counseling '
            'sessions as part of a weekend community screening drive.',
            'Doctors involved in the campaign said early detection remains one of the most '
            'effective ways to reduce stroke and heart-related emergencies.',
            'Residents were also given printed guides on low-salt meals and medication reminders '
            'for those already under treatment.',
        ],
    },
    {
        'title': 'Local startups pitch logistics tools at regional tech meetup',
        'category': 'Technology',
        'province': 'Western Visayas',
        'featured': True,
        'sticky': False,
        'breaking': False,
        'editors_pick': True,
        'image_seed': 'startup-pitch',
        'excerpt': (
            'Founders from Iloilo and Bacolod presented delivery-routing and inventory apps at a '
            'regional meetup focused on practical tools for small retailers.'
        ),
        'body': [
            'A regional technology meetup spotlighted logistics and retail software built by '
            'Western Visayas startups for neighborhood stores and courier partners.',
            'Pitch sessions emphasized offline-friendly features, simple dashboards, and pricing '
            'models suited to micro and small enterprises.',
            'Mentors from local incubators encouraged teams to pilot with real merchants before '
            'seeking larger funding rounds.',
        ],
    },
    {
        'title': 'Provincial athletes prepare for inter-regional games in August',
        'category': 'Sports',
        'province': 'Negros Occidental',
        'featured': False,
        'sticky': False,
        'breaking': False,
        'editors_pick': False,
        'image_seed': 'athletics',
        'excerpt': (
            'Training camps for athletics, swimming, and volleyball are underway as provincial '
            'delegations prepare for the August inter-regional sports meet.'
        ),
        'body': [
            'Coaches confirmed intensified training schedules for athletes selected to represent '
            'their provinces in the coming inter-regional games.',
            'Organizers said venues are being inspected for safety and spectator capacity, with '
            'final event lists expected before the end of the month.',
        ],
    },
    {
        'title': 'City council reviews flood-control timetable after heavy rains',
        'category': 'Politics',
        'province': 'Iloilo',
        'featured': False,
        'sticky': False,
        'breaking': False,
        'editors_pick': False,
        'image_seed': 'flood-control',
        'excerpt': (
            'Councilors asked for clearer timelines on drainage upgrades after recent downpours '
            'flooded several low-lying barangays during peak hours.'
        ),
        'body': [
            'Members of the city council pressed agencies for an updated flood-control timetable '
            'following repeated inundation in low-lying neighborhoods.',
            'Engineering offices presented completed segments and remaining packages, including '
            'pumping stations and cleared waterways still under procurement.',
            'Community leaders asked for earlier public advisories whenever heavy rainfall is '
            'expected during school and office rush hours.',
        ],
    },
    {
        'title': 'Cultural festival returns with outdoor stages and local crafts',
        'category': 'Entertainment',
        'province': 'Western Visayas',
        'featured': False,
        'sticky': False,
        'breaking': False,
        'editors_pick': False,
        'image_seed': 'festival-stage',
        'excerpt': (
            'Organizers revived an outdoor cultural festival featuring regional music, dance '
            'showcases, and craft booths from nearby municipalities.'
        ),
        'body': [
            'Festival organizers announced the return of outdoor stages after a quieter stretch of '
            'community events over the past seasons.',
            'This year’s program highlights traditional dance groups, contemporary local bands, '
            'and craft makers selling woven goods and food specialties.',
        ],
    },
    {
        'title': 'Opinion: Why local newsrooms still matter in a viral age',
        'category': 'Opinion',
        'province': 'Philippines',
        'featured': False,
        'sticky': False,
        'breaking': False,
        'editors_pick': True,
        'image_seed': 'newsroom',
        'excerpt': (
            'As social feeds move faster, community reporting remains essential for verifying '
            'what actually happened on the ground.'
        ),
        'body': [
            'Viral posts can travel farther than facts in a matter of minutes, which is why local '
            'newsrooms still play a critical public role.',
            'Reporters who know the streets, schools, and councils of a community can challenge '
            'rumors with context that national feeds often miss.',
            'Supporting credible local journalism is not nostalgia — it is infrastructure for an '
            'informed public.',
        ],
    },
    {
        'title': 'Weekend wellness fairs promote affordable meal planning',
        'category': 'Lifestyle',
        'province': 'Iloilo',
        'featured': False,
        'sticky': False,
        'breaking': False,
        'editors_pick': False,
        'image_seed': 'wellness-fair',
        'excerpt': (
            'Community wellness fairs offered budget meal demos, short fitness sessions, and '
            'checkups aimed at busy households.'
        ),
        'body': [
            'Weekend wellness fairs drew families looking for practical ways to eat better without '
            'raising weekly grocery costs.',
            'Nutrition volunteers demonstrated simple recipes using local produce, while nurses '
            'offered basic health checks at partner booths.',
        ],
    },
    {
        'title': 'Transport group seeks clearer provincial bus schedule updates',
        'category': 'Regional News',
        'province': 'Western Visayas',
        'featured': False,
        'sticky': False,
        'breaking': False,
        'editors_pick': False,
        'image_seed': 'bus-terminal',
        'excerpt': (
            'Commuter advocates asked terminals to post more reliable departure boards after '
            'repeated last-minute trip changes during peak weekends.'
        ),
        'body': [
            'Transport advocates urged provincial terminals to improve how schedule changes are '
            'announced to passengers, especially on Friday evenings and holiday weekends.',
            'Operators said they are testing digital boards and SMS advisories, though coverage '
            'still varies by terminal.',
        ],
    },
]


class Command(BaseCommand):
    help = (
        'Create published sample articles with sharp hero images for demos '
        'and free hosting where RSS scraping is blocked'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Recreate sample articles even if their slugs already exist',
        )

    def handle(self, *args, **options):
        force = options['force']
        author = self._ensure_author()
        created = 0
        updated = 0
        now = timezone.now()

        for index, item in enumerate(SAMPLE_ARTICLES):
            category, _ = Category.objects.get_or_create(
                slug=slugify(item['category']),
                defaults={'name': item['category'], 'is_active': True},
            )
            slug = slugify(item['title'])[:280]
            article = Article.objects.filter(slug=slug).first()
            if article and not force:
                if not article.hero_image:
                    self._assign_image(article, index, item.get('image_seed', slug))
                    updated += 1
                continue

            body_html = '\n'.join(f'<p>{paragraph}</p>' for paragraph in item['body'])
            if article and force:
                article.title = item['title']
                article.excerpt = item['excerpt']
                article.body = body_html
                article.category = category
                article.author = author
                article.province = item.get('province', '')
                article.is_featured = item.get('featured', False)
                article.is_sticky = item.get('sticky', False)
                article.is_breaking = item.get('breaking', False)
                article.is_editors_pick = item.get('editors_pick', False)
                article.status = 'published'
                article.published_at = now - timedelta(hours=index * 3)
                article.is_scraped = False
                article.verification_status = ''
                article.allow_comments = True
                ArticleService.prepare_article(article)
                article.save()
                self._assign_image(article, index, item.get('image_seed', slug), force=True)
                updated += 1
                self.stdout.write(f'  ~ updated {article.title}')
                continue

            article = Article(
                title=item['title'],
                slug=slug,
                excerpt=item['excerpt'],
                body=body_html,
                category=category,
                author=author,
                created_by=author.user if author else None,
                province=item.get('province', ''),
                status='published',
                published_at=now - timedelta(hours=index * 3),
                is_featured=item.get('featured', False),
                is_sticky=item.get('sticky', False),
                is_breaking=item.get('breaking', False),
                is_editors_pick=item.get('editors_pick', False),
                allow_comments=True,
                is_scraped=False,
                view_count=120 - index * 7,
            )
            ArticleService.prepare_article(article)
            article.save()

            tag_names = ['Regional', 'Community'] if item.get('province') else ['World', 'Analysis']
            for tag_name in tag_names:
                tag, _ = Tag.objects.get_or_create(
                    slug=slugify(tag_name),
                    defaults={'name': tag_name},
                )
                article.tags.add(tag)

            self._assign_image(article, index, item.get('image_seed', slug))
            created += 1
            self.stdout.write(f'  + {article.title}')

        self.stdout.write(self.style.SUCCESS(
            f'Sample articles ready: {created} created, {updated} updated.'
        ))

    def _ensure_author(self) -> AuthorProfile:
        role, _ = Role.objects.get_or_create(
            name='reporter',
            defaults={'display_name': 'Reporter', 'is_staff_role': True},
        )
        user, created = User.objects.get_or_create(
            email='reporter@nextgennews.com',
            defaults={
                'username': 'reporter',
                'first_name': 'Jane',
                'last_name': 'Reporter',
                'role': role,
                'is_email_verified': True,
            },
        )
        if created:
            user.set_password('Reporter@12345')
            user.save()

        author, _ = AuthorProfile.objects.get_or_create(
            slug='jane-reporter',
            defaults={
                'user': user,
                'display_name': 'Jane Reporter',
                'biography': 'Covers regional development, education, and community affairs.',
                'job_title': 'Senior Reporter',
                'is_featured': True,
            },
        )
        return author

    def _assign_image(self, article: Article, index: int, seed: str, force: bool = False) -> None:
        if self._download_stock_image(article, seed):
            return
        assign_hero_image(article, index=index, force=True if force or not article.hero_image else force)

    def _download_stock_image(self, article: Article, seed: str) -> bool:
        """Try a high-res public placeholder photo; fall back silently if blocked."""
        url = f'https://picsum.photos/seed/{seed}/1920/1080'
        try:
            response = requests.get(url, timeout=20, allow_redirects=True)
            response.raise_for_status()
            optimized = optimize_image_bytes(response.content, min_width=900)
            payload = optimized or response.content
            if len(payload) < 8000:
                return False
            filename = f'sample-{article.slug[:50]}.jpg'
            article.hero_image.save(filename, ContentFile(payload), save=True)
            article.hero_image_caption = 'Sample photo for demonstration'
            article.save(update_fields=['hero_image_caption'])
            return True
        except Exception:
            return False
