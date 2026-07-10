"""Analytics and visitor tracking models."""
from django.db import models


class VisitorLog(models.Model):
    """Individual visitor session logs."""

    session_key = models.CharField(max_length=40, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    referer = models.CharField(max_length=500, blank=True)
    path = models.CharField(max_length=500)
    device_type = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    visited_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-visited_at']
        indexes = [models.Index(fields=['visited_at', 'path'])]


class DailyAnalytics(models.Model):
    """Aggregated daily analytics."""

    date = models.DateField(unique=True)
    total_visitors = models.PositiveIntegerField(default=0)
    unique_visitors = models.PositiveIntegerField(default=0)
    page_views = models.PositiveIntegerField(default=0)
    bounce_rate = models.FloatField(default=0.0)
    avg_reading_time = models.FloatField(default=0.0)
    mobile_visitors = models.PositiveIntegerField(default=0)
    desktop_visitors = models.PositiveIntegerField(default=0)
    tablet_visitors = models.PositiveIntegerField(default=0)
    data = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name_plural = 'daily analytics'
        ordering = ['-date']

    def __str__(self) -> str:
        return f'Analytics for {self.date}'


class ArticleView(models.Model):
    """Detailed article view tracking."""

    article = models.ForeignKey('news.Article', on_delete=models.CASCADE, related_name='view_logs')
    session_key = models.CharField(max_length=40, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    referer = models.CharField(max_length=500, blank=True)
    reading_time_seconds = models.PositiveIntegerField(default=0)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-viewed_at']
