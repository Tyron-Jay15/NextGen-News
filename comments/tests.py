"""Tests for anonymous public comments."""
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from news.models import Article


class AnonymousCommentTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.article = Article.objects.create(
            title='Comment Test',
            slug='comment-test',
            body='body',
            status='published',
            published_at=timezone.now(),
            allow_comments=True,
        )

    def test_anonymous_comment_without_login(self):
        response = self.client.post(
            reverse('comments:post', kwargs={'slug': self.article.slug}),
            {'body': 'Great article!'},
        )
        self.assertEqual(response.status_code, 302)
        comment = self.article.comments.get(body='Great article!')
        self.assertTrue(comment.author_name.startswith('anonymous'))
        self.assertTrue(comment.is_guest)
        self.assertIsNone(comment.user_id)
        self.assertEqual(comment.status, 'approved')

    def test_generate_anonymous_name_format(self):
        from comments.services import generate_anonymous_name

        name = generate_anonymous_name()
        self.assertRegex(name, r'^anonymous\d+$')
