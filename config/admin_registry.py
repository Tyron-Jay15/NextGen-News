from django.contrib import admin

from advertisements.models import AdClick, AdImpression, Advertisement
from analytics.models import ArticleView, DailyAnalytics, VisitorLog
from authors.models import AuthorProfile
from categories.models import Category, Tag
from comments.models import Comment, CommentReport, CommentVote
from dashboard.models import AuditLog, SiteSetting
from media_library.models import MediaFile, MediaFolder
from notifications.models import Notification, NotificationPreference


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent', 'is_active', 'order']
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ['is_active', 'parent']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_trending', 'usage_count']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(AuthorProfile)
class AuthorProfileAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'slug', 'is_featured', 'total_views']
    prepopulated_fields = {'slug': ('display_name',)}
    search_fields = ['display_name']


@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ['title', 'ad_type', 'placement', 'is_active', 'click_count', 'impression_count']
    list_filter = ['ad_type', 'placement', 'is_active']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['article', 'user', 'status', 'likes', 'created_at']
    list_filter = ['status']
    actions = ['approve_comments', 'reject_comments']

    @admin.action(description='Approve selected comments')
    def approve_comments(self, request, queryset):
        queryset.update(status='approved')

    @admin.action(description='Reject selected comments')
    def reject_comments(self, request, queryset):
        queryset.update(status='rejected')


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not SiteSetting.objects.exists()


admin.site.register(MediaFolder)
admin.site.register(MediaFile)
admin.site.register(Notification)
admin.site.register(NotificationPreference)
admin.site.register(AuditLog)
admin.site.register(VisitorLog)
admin.site.register(DailyAnalytics)
admin.site.register(ArticleView)
admin.site.register(AdClick)
admin.site.register(AdImpression)
admin.site.register(CommentVote)
admin.site.register(CommentReport)
