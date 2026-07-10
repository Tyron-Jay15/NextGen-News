"""News admin configuration."""
from django.contrib import admin, messages

from news.models import (
    Article, ArticleMedia, ArticleRevision, Bookmark, NewsletterSubscriber,
    NewsSource, ReadingHistory, ScrapedItemLog,
)
from news.scrapers.service import NewsScraperService


class ArticleMediaInline(admin.TabularInline):
    model = ArticleMedia
    extra = 0


class ArticleRevisionInline(admin.TabularInline):
    model = ArticleRevision
    extra = 0
    readonly_fields = ['title', 'status', 'edited_by', 'created_at']
    can_delete = False


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'verification_status', 'is_scraped', 'author', 'category', 'view_count', 'published_at']
    list_filter = ['status', 'verification_status', 'is_scraped', 'is_featured', 'is_breaking', 'article_type', 'category', 'news_source']
    search_fields = ['title', 'subtitle', 'body', 'external_url']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['view_count', 'share_count', 'comment_count', 'duplicate_hash', 'external_guid', 'verified_at']
    inlines = [ArticleMediaInline, ArticleRevisionInline]
    date_hierarchy = 'published_at'


@admin.register(NewsSource)
class NewsSourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'source_type', 'category', 'is_active', 'auto_publish', 'articles_fetched', 'last_fetched_at']
    list_filter = ['is_active', 'auto_publish', 'source_type']
    search_fields = ['name', 'feed_url']
    actions = ['run_scraper_now', 'activate_sources', 'deactivate_sources']

    @admin.action(description='Scrape selected sources now')
    def run_scraper_now(self, request, queryset):
        total = 0
        for source in queryset:
            result = NewsScraperService.scrape_source(source)
            total += result['created']
        self.message_user(request, f'Scraping complete. {total} new article(s) posted.', messages.SUCCESS)

    @admin.action(description='Activate sources')
    def activate_sources(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description='Deactivate sources')
    def deactivate_sources(self, request, queryset):
        queryset.update(is_active=False)


@admin.register(ScrapedItemLog)
class ScrapedItemLogAdmin(admin.ModelAdmin):
    list_display = ['source', 'external_url', 'article', 'scraped_at']
    list_filter = ['source']
    search_fields = ['external_guid', 'external_url']
    readonly_fields = ['source', 'external_guid', 'external_url', 'article', 'scraped_at']


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'name', 'is_active', 'subscribed_at']
    list_filter = ['is_active']


admin.site.register(Bookmark)
admin.site.register(ReadingHistory)
