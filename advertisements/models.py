"""Advertisement management models."""
from django.db import models


class Advertisement(models.Model):
    """Advertisement placements with scheduling and tracking."""

    AD_TYPES = [
        ('banner', 'Banner'),
        ('sidebar', 'Sidebar'),
        ('inline', 'Inline'),
        ('popup', 'Popup'),
        ('video', 'Video'),
    ]

    PLACEMENTS = [
        ('homepage_top', 'Homepage Top'),
        ('homepage_sidebar', 'Homepage Sidebar'),
        ('article_top', 'Article Top'),
        ('article_inline', 'Article Inline'),
        ('article_sidebar', 'Article Sidebar'),
        ('category_sidebar', 'Category Sidebar'),
        ('footer', 'Footer'),
    ]

    title = models.CharField(max_length=200)
    ad_type = models.CharField(max_length=20, choices=AD_TYPES)
    placement = models.CharField(max_length=30, choices=PLACEMENTS)
    image = models.ImageField(upload_to='ads/', blank=True, null=True)
    video_url = models.URLField(blank=True)
    target_url = models.URLField()
    alt_text = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    click_count = models.PositiveIntegerField(default=0)
    impression_count = models.PositiveIntegerField(default=0)
    priority = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-priority', '-created_at']

    def __str__(self) -> str:
        return self.title


class AdClick(models.Model):
    """Track advertisement clicks."""

    advertisement = models.ForeignKey(Advertisement, on_delete=models.CASCADE, related_name='clicks')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    clicked_at = models.DateTimeField(auto_now_add=True)


class AdImpression(models.Model):
    """Track advertisement impressions."""

    advertisement = models.ForeignKey(Advertisement, on_delete=models.CASCADE, related_name='impressions')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    page_url = models.CharField(max_length=500, blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
