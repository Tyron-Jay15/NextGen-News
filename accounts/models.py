"""User accounts, roles, and authentication models."""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class Role(models.Model):
    """Role-based access control roles."""

    ROLE_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('admin', 'Admin'),
        ('chief_editor', 'Chief Editor'),
        ('editor', 'Editor'),
        ('reporter', 'Reporter'),
        ('photographer', 'Photographer'),
        ('contributor', 'Contributor'),
        ('moderator', 'Moderator'),
        ('registered_reader', 'Registered Reader'),
        ('guest', 'Guest'),
    ]

    name = models.CharField(max_length=50, choices=ROLE_CHOICES, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    permissions = models.JSONField(default=dict, blank=True)
    is_staff_role = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.display_name


class User(AbstractUser):
    """Custom user model with role support."""

    email = models.EmailField(_('email address'), unique=True)
    role = models.ForeignKey(
        Role, on_delete=models.SET_NULL, null=True, blank=True, related_name='users'
    )
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True)
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=64, blank=True)
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=32, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    newsletter_subscribed = models.BooleanField(default=False)
    dark_mode = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        ordering = ['-date_joined']

    def __str__(self) -> str:
        return self.email

    @property
    def role_name(self) -> str:
        return self.role.name if self.role else 'guest'

    def has_role(self, *roles: str) -> bool:
        return self.role_name in roles

    def can_edit_articles(self) -> bool:
        return self.role_name in (
            'super_admin', 'admin', 'chief_editor', 'editor', 'reporter', 'contributor'
        )

    def can_publish_articles(self) -> bool:
        return self.role_name in ('super_admin', 'admin', 'chief_editor')

    def can_moderate_comments(self) -> bool:
        return self.role_name in ('super_admin', 'admin', 'moderator', 'chief_editor', 'editor')

    @property
    def is_staff_member(self) -> bool:
        """True for editorial/admin users who manage the site."""
        if self.is_staff or self.is_superuser:
            return True
        return bool(self.role and self.role.is_staff_role)


class UserProfile(models.Model):
    """Extended user profile information."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    province = models.CharField(max_length=100, blank=True)
    municipality = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    website = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    facebook = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    preferred_categories = models.ManyToManyField(
        'categories.Category', blank=True, related_name='preferred_by'
    )

    def __str__(self) -> str:
        return f'Profile: {self.user.email}'
