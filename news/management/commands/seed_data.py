"""Seed essential admin accounts, roles, and categories — no demo articles."""
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from accounts.models import Role, User
from authors.models import AuthorProfile
from categories.models import Category, Tag
from dashboard.models import SiteSetting


class Command(BaseCommand):
    help = 'Seed roles, admin user, categories, and RSS sources (no fake demo articles)'

    def handle(self, *args, **options):
        self.stdout.write('Seeding NextGen News...')

        roles_data = [
            ('super_admin', 'Super Admin', True),
            ('admin', 'Admin', True),
            ('chief_editor', 'Chief Editor', True),
            ('editor', 'Editor', True),
            ('reporter', 'Reporter', True),
            ('photographer', 'Photographer', True),
            ('contributor', 'Contributor', True),
            ('moderator', 'Moderator', True),
            ('registered_reader', 'Registered Reader', False),
            ('guest', 'Guest', False),
        ]
        for name, display, is_staff in roles_data:
            Role.objects.get_or_create(
                name=name,
                defaults={'display_name': display, 'is_staff_role': is_staff},
            )

        admin_role = Role.objects.get(name='super_admin')
        if not User.objects.filter(email='admin@nextgennews.com').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@nextgennews.com',
                password='Admin@12345',
                first_name='System',
                last_name='Administrator',
            )
            admin.role = admin_role
            admin.is_email_verified = True
            admin.save()
            self.stdout.write(self.style.SUCCESS('Created admin: admin@nextgennews.com / Admin@12345'))

        reporter_role = Role.objects.get(name='reporter')
        reporter, created = User.objects.get_or_create(
            email='reporter@nextgennews.com',
            defaults={
                'username': 'reporter',
                'first_name': 'Jane',
                'last_name': 'Reporter',
                'role': reporter_role,
                'is_email_verified': True,
            },
        )
        if created:
            reporter.set_password('Reporter@12345')
            reporter.save()

        SiteSetting.load()

        categories_data = [
            ('Politics', 'bi-bank', None),
            ('Business', 'bi-briefcase', None),
            ('Sports', 'bi-trophy', None),
            ('Technology', 'bi-cpu', None),
            ('Health', 'bi-heart-pulse', None),
            ('Education', 'bi-book', None),
            ('Entertainment', 'bi-film', None),
            ('Lifestyle', 'bi-stars', None),
            ('Opinion', 'bi-chat-quote', None),
            ('Regional News', 'bi-geo-alt', None),
            ('International', 'bi-globe', None),
        ]
        cat_map = {}
        for name, icon, parent in categories_data:
            cat, _ = Category.objects.get_or_create(
                slug=slugify(name),
                defaults={'name': name, 'icon': icon, 'parent': parent, 'is_active': True},
            )
            cat_map[name] = cat

        tags = ['Breaking', 'Analysis', 'Exclusive', 'Investigation', 'Trending']
        tag_objs = []
        for t in tags:
            tag, _ = Tag.objects.get_or_create(slug=slugify(t), defaults={'name': t, 'is_trending': t == 'Trending'})
            tag_objs.append(tag)

        author, _ = AuthorProfile.objects.get_or_create(
            slug='jane-reporter',
            defaults={
                'user': reporter,
                'display_name': 'Jane Reporter',
                'biography': 'Award-winning journalist covering politics and business.',
                'job_title': 'Senior Reporter',
                'is_featured': True,
            },
        )

        call_command('setup_scraper_sources')
        call_command('seed_public_articles')

        self.stdout.write(self.style.SUCCESS(
            'Seed complete. Sample articles are published for public browsing. '
            'On paid hosting you can also run `python manage.py scrape_news` for live RSS.'
        ))
