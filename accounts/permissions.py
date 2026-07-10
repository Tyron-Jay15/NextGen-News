"""Role-based permissions definitions."""
from functools import wraps

from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied


ROLE_PERMISSIONS = {
    'super_admin': ['*'],
    'admin': [
        'manage_users', 'manage_articles', 'manage_categories', 'manage_ads',
        'manage_comments', 'view_analytics', 'manage_settings', 'publish_articles',
    ],
    'chief_editor': [
        'manage_articles', 'manage_categories', 'publish_articles',
        'manage_comments', 'view_analytics', 'approve_articles',
    ],
    'editor': ['manage_articles', 'review_articles', 'manage_comments'],
    'reporter': ['create_articles', 'edit_own_articles'],
    'photographer': ['upload_media', 'edit_own_articles'],
    'contributor': ['create_articles', 'edit_own_articles'],
    'moderator': ['manage_comments'],
    'registered_reader': ['comment', 'bookmark'],
    'guest': ['read', 'comment_if_allowed'],
}


def has_permission(user, permission: str) -> bool:
    if not user.is_authenticated:
        return permission in ROLE_PERMISSIONS.get('guest', [])
    if user.is_superuser:
        return True
    role = user.role_name
    perms = ROLE_PERMISSIONS.get(role, [])
    return '*' in perms or permission in perms


def permission_required(permission: str):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not has_permission(request.user, permission):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def role_required(*roles):
    def check(user):
        return user.is_authenticated and (user.is_superuser or user.role_name in roles)
    return user_passes_test(check)
