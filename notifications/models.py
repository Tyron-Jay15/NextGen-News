"""Notification models."""
from django.conf import settings
from django.db import models


class Notification(models.Model):
    """In-app notifications."""

    NOTIFICATION_TYPES = [
        ('system', 'System'),
        ('breaking_news', 'Breaking News'),
        ('comment_reply', 'Comment Reply'),
        ('article_approved', 'Article Approved'),
        ('article_published', 'Article Published'),
        ('comment_moderation', 'Comment Moderation'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications'
    )
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.title} for {self.user.email}'


class NotificationPreference(models.Model):
    """User notification preferences."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_prefs'
    )
    email_enabled = models.BooleanField(default=True)
    push_enabled = models.BooleanField(default=True)
    in_app_enabled = models.BooleanField(default=True)
    breaking_news_alerts = models.BooleanField(default=True)
    comment_replies = models.BooleanField(default=True)
    article_updates = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f'Notification prefs for {self.user.email}'
