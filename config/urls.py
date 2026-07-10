"""NextGen News Management System — URL Configuration."""
import config.admin_registry  # noqa: F401 — register models with admin
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic import TemplateView

from news.sitemaps import ArticleSitemap, CategorySitemap, GoogleNewsSitemap

sitemaps = {
    'articles': ArticleSitemap,
    'categories': CategorySitemap,
    'google_news': GoogleNewsSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('ckeditor5/', include('django_ckeditor_5.urls')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    path('search/', include('search.urls', namespace='search')),
    path('api/', include('api.urls', namespace='api')),
    path('notifications/', include('notifications.urls', namespace='notifications')),
    path('authors/', include('authors.urls', namespace='authors')),
    path('categories/', include('categories.urls', namespace='categories')),
    path('comments/', include('comments.urls', namespace='comments')),
    path('', include('news.urls', namespace='news')),
    path(
        'sitemap.xml',
        sitemap,
        {'sitemaps': sitemaps},
        name='django.contrib.sitemaps.views.sitemap',
    ),
    path(
        'robots.txt',
        TemplateView.as_view(template_name='robots.txt', content_type='text/plain'),
        name='robots',
    ),
]

# Serve uploaded media in production when SERVE_MEDIA=True (PythonAnywhere).
# NOTE: django.conf.urls.static.static() is a no-op when DEBUG=False, so we
# register the view ourselves for hosting platforms without a separate media CDN.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
elif getattr(settings, 'SERVE_MEDIA', False):
    from django.urls import re_path
    from django.views.static import serve

    urlpatterns += [
        re_path(
            r'^media/(?P<path>.*)$',
            serve,
            {'document_root': settings.MEDIA_ROOT},
        ),
    ]

admin.site.site_header = 'NextGen News Administration'
admin.site.site_title = 'NextGen News Admin'
admin.site.index_title = 'News Management System'
