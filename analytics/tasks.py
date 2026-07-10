"""Aggregate daily analytics via Celery."""
from celery import shared_task
from django.db.models import Count
from django.utils import timezone

from analytics.models import DailyAnalytics, VisitorLog


@shared_task
def aggregate_daily_analytics():
    today = timezone.now().date()
    logs = VisitorLog.objects.filter(visited_at__date=today)
    unique = logs.values('session_key').distinct().count()
    mobile = logs.filter(device_type='mobile').values('session_key').distinct().count()
    desktop = logs.filter(device_type='desktop').values('session_key').distinct().count()
    tablet = logs.filter(device_type='tablet').values('session_key').distinct().count()

    DailyAnalytics.objects.update_or_create(
        date=today,
        defaults={
            'total_visitors': logs.count(),
            'unique_visitors': unique,
            'page_views': logs.count(),
            'mobile_visitors': mobile,
            'desktop_visitors': desktop,
            'tablet_visitors': tablet,
        },
    )


@shared_task
def publish_scheduled_articles():
    from news.models import Article
    from news.services import ArticleService

    due = Article.objects.filter(status='scheduled', scheduled_at__lte=timezone.now())
    for article in due:
        ArticleService.transition_status(article, 'published', article.created_by)
