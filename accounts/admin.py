"""Account admin configuration."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from accounts.models import Role, User, UserProfile


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'name', 'is_staff_role', 'created_at']
    search_fields = ['name', 'display_name']


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    extra = 0


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'role', 'is_active', 'is_email_verified', 'date_joined']
    list_filter = ['role', 'is_active', 'is_staff', 'is_email_verified']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-date_joined']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('NextGen News', {
            'fields': ('role', 'phone', 'avatar', 'bio', 'is_email_verified', 'two_factor_enabled',
                       'newsletter_subscribed', 'dark_mode'),
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('NextGen News', {'fields': ('email', 'role')}),
    )
    inlines = [UserProfileInline]
