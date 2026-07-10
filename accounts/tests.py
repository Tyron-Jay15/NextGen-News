from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import Role, User


class LogoutViewTest(TestCase):
    def setUp(self):
        role = Role.objects.create(name='admin', display_name='Admin', is_staff_role=True)
        self.user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='Admin@12345',
            role=role,
            is_staff=True,
        )
        self.client = Client()
        self.client.force_login(self.user)

    def test_logout_requires_post(self):
        response = self.client.get(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 405)

    def test_logout_post_redirects_home(self):
        response = self.client.post(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('news:home'))
