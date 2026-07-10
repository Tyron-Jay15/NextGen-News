"""Unit and integration tests for NextGen News."""
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role, User
from categories.models import Category, Tag
from news.models import Article
from news.services import ArticleService
from authors.models import AuthorProfile


class RoleModelTest(TestCase):
    def test_create_role(self):
        role = Role.objects.create(name='editor', display_name='Editor', is_staff_role=True)
        self.assertEqual(str(role), 'Editor')


class UserModelTest(TestCase):
    def setUp(self):
        self.role = Role.objects.create(name='reporter', display_name='Reporter', is_staff_role=True)

    def test_user_can_edit_articles(self):
        user = User.objects.create_user(
            username='test', email='test@test.com', password='Test@12345', role=self.role
        )
        self.assertTrue(user.can_edit_articles())

    def test_email_login_backend(self):
        User.objects.create_user(
            username='login',
            email='login@test.com',
            password='Test@12345',
            is_staff=True,
        )
        client = Client()
        response = client.post(reverse('accounts:admin_login'), {
            'username': 'login@test.com',
            'password': 'Test@12345',
        })
        self.assertEqual(response.status_code, 302)


class ArticleServiceTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='News', slug='news')
        self.user = User.objects.create_user(username='author', email='a@test.com', password='pass')
        self.author = AuthorProfile.objects.create(
            user=self.user, display_name='Author', slug='author'
        )

    def test_reading_time_estimation(self):
        article = Article.objects.create(
            title='Test Article',
            slug='test-article',
            body='<p>' + 'word ' * 400 + '</p>',
            author=self.author,
            category=self.category,
            status='published',
            published_at=timezone.now(),
        )
        ArticleService.prepare_article(article)
        self.assertGreaterEqual(article.reading_time_minutes, 1)

    def test_get_published(self):
        Article.objects.create(
            title='Published', slug='published', body='content',
            status='published', published_at=timezone.now(),
        )
        Article.objects.create(title='Draft', slug='draft', body='content', status='draft')
        self.assertEqual(ArticleService.get_published().count(), 1)


class PublicViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Tech', slug='tech')

    def test_homepage_loads(self):
        response = self.client.get(reverse('news:home'))
        self.assertEqual(response.status_code, 200)

    def test_article_detail(self):
        article = Article.objects.create(
            title='Test News Story',
            slug='test-news-story',
            body='<p>Content here</p>',
            category=self.category,
            status='published',
            published_at=timezone.now(),
        )
        response = self.client.get(reverse('news:article_detail', kwargs={'slug': article.slug}))
        self.assertEqual(response.status_code, 200)
        article.refresh_from_db()
        self.assertEqual(article.view_count, 1)

    def test_search_page(self):
        response = self.client.get(reverse('search:search'), {'q': 'test'})
        self.assertEqual(response.status_code, 200)


class APITest(TestCase):
    def setUp(self):
        self.client = Client()
        Article.objects.create(
            title='API Test Article',
            slug='api-test',
            body='content',
            status='published',
            published_at=timezone.now(),
        )

    def test_articles_api_list(self):
        response = self.client.get('/api/articles/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['results']), 1)

    def test_search_autocomplete(self):
        response = self.client.get(reverse('search:autocomplete'), {'q': 'API'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.json())


class EditorialWorkflowTest(TestCase):
    def setUp(self):
        chief_role = Role.objects.create(name='chief_editor', display_name='Chief Editor', is_staff_role=True)
        self.chief = User.objects.create_user(
            username='chief', email='chief@test.com', password='pass', role=chief_role
        )
        self.article = Article.objects.create(title='Workflow Test', slug='workflow', body='body', status='draft')

    def test_publish_workflow(self):
        ArticleService.transition_status(self.article, 'pending_review', self.chief)
        self.article.refresh_from_db()
        self.assertEqual(self.article.status, 'pending_review')
        ArticleService.transition_status(self.article, 'fact_check', self.chief)
        ArticleService.transition_status(self.article, 'approved', self.chief)
        ArticleService.transition_status(self.article, 'published', self.chief)
        self.article.refresh_from_db()
        self.assertEqual(self.article.status, 'published')
        self.assertIsNotNone(self.article.published_at)


class VideoEmbedTest(TestCase):
    def test_parse_youtube_url(self):
        from news.utils.video import parse_video_url

        info = parse_video_url('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
        self.assertIsNotNone(info)
        self.assertEqual(info.provider, 'youtube')
        self.assertEqual(info.video_id, 'dQw4w9WgXcQ')
        self.assertIn('youtube-nocookie.com/embed/', info.embed_url)
        self.assertIn('hqdefault.jpg', info.thumbnail_url)

    def test_article_video_on_detail_page(self):
        Article.objects.create(
            title='Video Story',
            slug='video-story',
            body='<p>Watch below.</p>',
            status='published',
            published_at=timezone.now(),
            video_url='https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        )
        response = Client().get(reverse('news:article_detail', kwargs={'slug': 'video-story'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'youtube-nocookie.com/embed/dQw4w9WgXcQ')


class ScraperParserTest(TestCase):
    def test_split_google_news_title(self):
        from news.scrapers.parsers import split_google_news_title

        headline, publisher = split_google_news_title('Big story breaks - BBC')
        self.assertEqual(headline, 'Big story breaks')
        self.assertEqual(publisher, 'BBC')

    def test_extract_bbc_body(self):
        from news.scrapers.parsers import extract_article_body

        sample = '''
        <html><body><article>
        <div data-component="text-block"><p>First paragraph of the news story with enough words to pass validation easily here.</p></div>
        <div data-component="text-block"><p>Second paragraph continues the report with additional detail for readers.</p></div>
        </article></body></html>
        '''
        body = extract_article_body(sample, 'https://www.bbc.co.uk/news/articles/test')
        text = body.replace('<p>', '').replace('</p>', '')
        self.assertIn('First paragraph', text)
        self.assertGreater(len(text), 120)


class CredibilityScannerTest(TestCase):
    def test_rejects_demo_content(self):
        from news.scrapers.verification import CredibilityScanner

        result = CredibilityScanner.scan(
            title='Demo Article',
            body_html='<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. ' * 5 + '</p>',
            external_url='https://www.bbc.co.uk/news/articles/test',
        )
        self.assertFalse(result.is_legitimate)
        self.assertEqual(result.score, 0.0)

    def test_accepts_trusted_bbc_article(self):
        from news.scrapers.verification import CredibilityScanner

        body = '<p>' + ('Real BBC news paragraph with enough words to pass the minimum length check. ' * 4) + '</p>'
        result = CredibilityScanner.scan(
            title='World leaders meet for climate summit updates',
            body_html=body,
            external_url='https://www.bbc.co.uk/news/articles/test123',
            source_name='BBC World News',
        )
        self.assertTrue(result.is_legitimate)
        self.assertGreaterEqual(result.score, 70)

    def test_accepts_panay_news_article(self):
        from news.scrapers.verification import CredibilityScanner

        body = '<p>' + ('ILOILO City local report with enough words for verification from Panay News Western Visayas. ' * 3) + '</p>'
        result = CredibilityScanner.scan(
            title='Iloilo City launches new community health program',
            body_html=body,
            external_url='https://www.panaynews.net/sample-local-story/',
            source_name='Panay News - Iloilo',
        )
        self.assertTrue(result.is_legitimate)


class SucuriBypassTest(TestCase):
    CHALLENGE_HTML = '''
    <html><title>You are being redirected...</title>
    <script>var S='cj0nZScgKyBTdHJpbmcuZnJvbUNoYXJDb2RlKDU2KSArICIwIiArIFN0cmluZy5mcm9tQ2hhckNvZGUoNTApICsgU3RyaW5nLmZyb21DaGFyQ29kZSg1MCkgKyAiMyIgKyAiOCIgKyBTdHJpbmcuZnJvbUNoYXJDb2RlKDk4KSArIFN0cmluZy5mcm9tQ2hhckNvZGUoMTAwKSArIFN0cmluZy5mcm9tQ2hhckNvZGUoMTAyKSArICczJyArICc5JyArIFN0cmluZy5mcm9tQ2hhckNvZGUoNDgpICsgIjkiICsgU3RyaW5nLmZyb21DaGFyQ29kZSg1MykgKyBTdHJpbmcuZnJvbUNoYXJDb2RlKDk3KSArICc0JyArICIwIiArICdkJyArIFN0cmluZy5mcm9tQ2hhckNvZGUoNTMpICsgImMiICsgImEiICsgJ2MnICsgIjciICsgU3RyaW5nLmZyb21DaGFyQ29kZSg1MCkgKyBTdHJpbmcuZnJvbUNoYXJDb2RlKDUwKSArICcwJyArICJmIiArICJhIiArIFN0cmluZy5mcm9tQ2hhckNvZGUoNTUpICsgU3RyaW5nLmZyb21DaGFyQ29kZSg1NCkgKyBTdHJpbmcuZnJvbUNoYXJDb2RlKDUxKSArICcnO2RvY3VtZW50LmNvb2tpZT0ncycrJ3UnKydjJysndScrJ3InKydpJysnXycrJ2MnKydsJysnbycrJ3UnKydkJysncCcrJ3InKydvJysneCcrJ3knKydfJysndScrJ3UnKydpJysnZCcrJ18nKyc0JysnZScrJzUnKyc3JysnNicrJ2UnKydhJysnNicrJzcnKyI9IiArIHIgKyAnO3BhdGg9LzttYXgtYWdlPTg2NDAwJzsgbG9jYXRpb24ucmVsb2FkKCk7';L=S.length;U=0;r='';var A='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';for(u=0;u<64;u++){s[A.charAt(u)]=u;}for(i=0;i<L;i++){c=s[S.charAt(i)];U=(U<<6)+c;l+=6;while(l>=8){((a=(U>>>(l-=8))&0xff)||(i<(L-2)))&&(r+=w(a));}}e(r);</script></html>
    '''

    def test_extracts_sucuri_cookie(self):
        from news.scrapers.sucuri import extract_sucuri_cookie, is_sucuri_challenge

        self.assertTrue(is_sucuri_challenge(self.CHALLENGE_HTML))
        cookie = extract_sucuri_cookie(self.CHALLENGE_HTML)
        self.assertIsNotNone(cookie)
        name, value = cookie
        self.assertTrue(name.startswith('sucuri_cloudproxy_uuid_'))
        self.assertGreaterEqual(len(value), 16)
