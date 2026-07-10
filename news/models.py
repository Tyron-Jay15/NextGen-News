"""News article models with editorial workflow."""
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field


class Article(models.Model):
    """Core news article with full editorial workflow."""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_review', 'Pending Review'),
        ('fact_check', 'Fact Checking'),
        ('approved', 'Approved'),
        ('scheduled', 'Scheduled'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    ARTICLE_TYPE_CHOICES = [
        ('news', 'News'),
        ('opinion', 'Opinion'),
        ('feature', 'Feature'),
        ('breaking', 'Breaking'),
        ('analysis', 'Analysis'),
    ]

    title = models.CharField(max_length=300)
    subtitle = models.CharField(max_length=500, blank=True)
    slug = models.SlugField(max_length=320, unique=True)
    excerpt = models.TextField(blank=True, max_length=500)
    body = CKEditor5Field('Content', config_name='article')
    hero_image = models.ImageField(upload_to='articles/hero/', blank=True, null=True)
    hero_image_caption = models.CharField(max_length=255, blank=True)
    video_url = models.URLField(
        blank=True,
        help_text='Optional YouTube or Vimeo URL shown as featured video on the article page.',
    )
    author = models.ForeignKey(
        'authors.AuthorProfile', on_delete=models.SET_NULL, null=True, related_name='articles'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_articles'
    )
    category = models.ForeignKey(
        'categories.Category', on_delete=models.SET_NULL, null=True, related_name='articles'
    )
    tags = models.ManyToManyField('categories.Tag', blank=True, related_name='articles')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', db_index=True)
    article_type = models.CharField(max_length=20, choices=ARTICLE_TYPE_CHOICES, default='news')

    # Editorial flags
    is_featured = models.BooleanField(default=False, db_index=True)
    is_breaking = models.BooleanField(default=False, db_index=True)
    is_editors_pick = models.BooleanField(default=False)
    is_sticky = models.BooleanField(default=False)
    allow_comments = models.BooleanField(default=True)

    # Location
    province = models.CharField(max_length=100, blank=True, db_index=True)
    municipality = models.CharField(max_length=100, blank=True, db_index=True)

    # Metrics
    view_count = models.PositiveIntegerField(default=0, db_index=True)
    share_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    reading_time_minutes = models.PositiveSmallIntegerField(default=1)

    # SEO
    seo_title = models.CharField(max_length=70, blank=True)
    seo_description = models.CharField(max_length=160, blank=True)
    seo_keywords = models.CharField(max_length=255, blank=True)
    canonical_url = models.URLField(blank=True)
    og_image = models.ImageField(upload_to='articles/og/', blank=True, null=True)

    # AI-ready fields
    ai_summary = models.TextField(blank=True)
    ai_score = models.FloatField(null=True, blank=True, help_text='Credibility score from automated scan (0-100).')
    duplicate_hash = models.CharField(max_length=64, blank=True, db_index=True)

    VERIFICATION_STATUS = [
        ('pending', 'Pending Scan'),
        ('verified', 'Verified Legitimate'),
        ('rejected', 'Rejected'),
    ]
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS,
        blank=True,
        default='',
        db_index=True,
    )
    verification_notes = models.TextField(blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    # Scheduling
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    # Workflow tracking
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviewed_articles'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approved_articles'
    )

    # External / scraped content
    is_scraped = models.BooleanField(default=False, db_index=True)
    external_url = models.URLField(blank=True, db_index=True)
    external_guid = models.CharField(max_length=500, blank=True, db_index=True)
    news_source = models.ForeignKey(
        'NewsSource', on_delete=models.SET_NULL, null=True, blank=True, related_name='articles'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['status', '-published_at']),
            models.Index(fields=['category', 'status', '-published_at']),
            models.Index(fields=['-view_count']),
        ]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:300]
            self.slug = base
            counter = 1
            while Article.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f'{base}-{counter}'
                counter += 1
        if not self.seo_title:
            self.seo_title = self.title[:70]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('news:article_detail', kwargs={'slug': self.slug})

    @property
    def hero_url(self) -> str:
        """
        Public URL for the article image.

        Prefers packaged static samples (reliable on PythonAnywhere via WhiteNoise),
        then falls back to uploaded media files.
        """
        from django.contrib.staticfiles.finders import find
        from django.templatetags.static import static

        sample_name = f'img/samples/{self.slug}.jpg'
        if find(sample_name):
            return static(sample_name)
        if self.hero_image:
            try:
                return self.hero_image.url
            except ValueError:
                pass
        return ''

    @property
    def has_hero(self) -> bool:
        return bool(self.hero_url)

    @property
    def is_published(self) -> bool:
        return self.status == 'published' and self.published_at and self.published_at <= timezone.now()

    @property
    def has_video(self) -> bool:
        return bool(self.video_url)

    @property
    def video_info(self):
        if not self.video_url:
            return None
        from news.utils.video import parse_video_url
        return parse_video_url(self.video_url)

    def increment_views(self):
        Article.objects.filter(pk=self.pk).update(view_count=models.F('view_count') + 1)
        self.refresh_from_db(fields=['view_count'])


class ArticleRevision(models.Model):
    """Version history for articles."""

    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='revisions')
    title = models.CharField(max_length=300)
    body = models.TextField()
    status = models.CharField(max_length=20)
    edited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    change_summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'Revision of {self.article.title} at {self.created_at}'


class ArticleMedia(models.Model):
    """Embedded media within articles."""

    MEDIA_TYPES = [('image', 'Image'), ('video', 'Video'), ('audio', 'Audio'), ('gallery', 'Gallery')]

    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='media_items')
    media_type = models.CharField(max_length=20, choices=MEDIA_TYPES)
    file = models.FileField(upload_to='articles/media/', blank=True, null=True)
    url = models.URLField(blank=True)
    caption = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']


class Bookmark(models.Model):
    """User saved articles."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookmarks')
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='bookmarks')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'article']
        ordering = ['-created_at']


class ReadingHistory(models.Model):
    """Track user reading history."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reading_history')
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='readers')
    read_at = models.DateTimeField(auto_now=True)
    read_duration_seconds = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = 'reading histories'
        unique_together = ['user', 'article']
        ordering = ['-read_at']


class NewsletterSubscriber(models.Model):
    """Newsletter subscription management."""

    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    confirmation_token = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ['-subscribed_at']

    def __str__(self) -> str:
        return self.email


class NewsSource(models.Model):
    """External news feed or page to scrape automatically."""

    SOURCE_TYPES = [
        ('rss', 'RSS Feed'),
        ('html', 'HTML Page'),
    ]

    name = models.CharField(max_length=150)
    feed_url = models.URLField(help_text='RSS feed URL or page URL to scrape')
    source_type = models.CharField(max_length=10, choices=SOURCE_TYPES, default='rss')
    category = models.ForeignKey(
        'categories.Category', on_delete=models.SET_NULL, null=True, blank=True, related_name='news_sources'
    )
    is_active = models.BooleanField(default=True)
    is_trusted = models.BooleanField(
        default=True,
        help_text='Only trusted RSS sources are allowed through the credibility scanner.',
    )
    auto_publish = models.BooleanField(
        default=True,
        help_text='Publish verified scraped articles automatically after the legitimacy scan.',
    )
    fetch_full_content = models.BooleanField(
        default=False, help_text='Attempt to fetch full article body from source link'
    )
    attribution_name = models.CharField(max_length=100, blank=True, help_text='Credit line shown on articles')
    last_fetched_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    articles_fetched = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class ScrapedItemLog(models.Model):
    """Track scraped items to prevent duplicates."""

    source = models.ForeignKey(NewsSource, on_delete=models.CASCADE, related_name='scraped_items')
    external_guid = models.CharField(max_length=500, unique=True)
    external_url = models.URLField()
    article = models.OneToOneField(
        Article, on_delete=models.SET_NULL, null=True, blank=True, related_name='scrape_log'
    )
    scraped_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-scraped_at']

    def __str__(self) -> str:
        return f'{self.source.name}: {self.external_guid[:60]}'
