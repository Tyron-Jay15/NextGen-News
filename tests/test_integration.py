"""Integration tests across apps."""
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role, User
from comments.models import Comment
from news.models import Article


class CommentIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='reader', email='r@test.com', password='pass')
        self.article = Article.objects.create(
            title='Comment Test', slug='comment-test', body='body',
            status='published', published_at=timezone.now(), allow_comments=True,
        )

    def test_anonymous_comment(self):
        response = self.client.post(reverse('comments:post', kwargs={'slug': self.article.slug}), {
            'body': 'Great article!',
        })
        self.assertEqual(response.status_code, 302)
        comment = Comment.objects.get(article=self.article, body='Great article!')
        self.assertTrue(comment.author_name.startswith('anonymous'))
        self.assertEqual(comment.status, 'approved')


class DashboardIntegrationTest(TestCase):
    def setUp(self):
        editor_role = Role.objects.create(name='editor', display_name='Editor', is_staff_role=True)
        self.editor = User.objects.create_user(
            username='editor', email='editor@test.com', password='pass', role=editor_role
        )

    def test_dashboard_access(self):
        self.client.login(username='editor@test.com', password='pass')
        response = self.client.get(reverse('dashboard:home'))
        self.assertEqual(response.status_code, 200)
