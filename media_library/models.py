"""Media library models."""
from django.conf import settings
from django.db import models


class MediaFolder(models.Model):
    """Organize media files in folders."""

    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='children'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class MediaFile(models.Model):
    """Central media library for images, videos, PDFs, and audio."""

    FILE_TYPES = [
        ('image', 'Image'), ('video', 'Video'), ('pdf', 'PDF'), ('audio', 'Audio'), ('other', 'Other')
    ]

    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='library/%Y/%m/')
    file_type = models.CharField(max_length=20, choices=FILE_TYPES, default='image')
    folder = models.ForeignKey(
        MediaFolder, on_delete=models.SET_NULL, null=True, blank=True, related_name='files'
    )
    alt_text = models.CharField(max_length=255, blank=True)
    caption = models.TextField(blank=True)
    file_size = models.PositiveIntegerField(default=0)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    is_watermarked = models.BooleanField(default=False)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.title
