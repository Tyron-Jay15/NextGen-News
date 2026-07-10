"""Author profile models."""
from django.conf import settings
from django.db import models
from django.urls import reverse


class AuthorProfile(models.Model):
    """Extended author profile linked to user account."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='author_profile'
    )
    display_name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160, unique=True)
    biography = models.TextField(blank=True)
    photo = models.ImageField(upload_to='authors/', blank=True, null=True)
    job_title = models.CharField(max_length=100, blank=True)
    twitter = models.URLField(blank=True)
    facebook = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    website = models.URLField(blank=True)
    is_featured = models.BooleanField(default=False)
    total_views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['display_name']

    def __str__(self) -> str:
        return self.display_name

    def get_absolute_url(self):
        return reverse('authors:detail', kwargs={'slug': self.slug})

    @property
    def article_count(self) -> int:
        return self.articles.filter(status='published').count()
