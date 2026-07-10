"""Analytics services."""
from datetime import date

from django.db.models import Count
from django.utils import timezone

from analytics.models import ArticleView, DailyAnalytics, VisitorLog
from config.utils import detect_device_type, get_client_ip


class AnalyticsService:
    @staticmethod
    def log_visit(request):
        if not request.session.session_key:
            request.session.save()
        VisitorLog.objects.create(
            session_key=request.session.session_key or '',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            referer=request.META.get('HTTP_REFERER', '')[:500],
            path=request.path[:500],
            device_type=detect_device_type(request.META.get('HTTP_USER_AGENT', '')),
        )

    @staticmethod
    def log_article_view(request, article, reading_time: int = 0):
        ArticleView.objects.create(
            article=article,
            session_key=request.session.session_key or '',
            ip_address=get_client_ip(request),
            referer=request.META.get('HTTP_REFERER', '')[:500],
            reading_time_seconds=reading_time,
        )

    @staticmethod
    def get_dashboard_stats() -> dict:
        from news.models import Article
        from accounts.models import User
        today = date.today()
        return {
            'total_articles': Article.objects.count(),
            'published_articles': Article.objects.filter(status='published').count(),
            'draft_articles': Article.objects.filter(status='draft').count(),
            'total_users': User.objects.count(),
            'today_visitors': VisitorLog.objects.filter(visited_at__date=today).values('session_key').distinct().count(),
            'total_views': Article.objects.aggregate(total=Count('view_count'))['total'] or 0,
            'top_articles': Article.objects.filter(status='published').order_by('-view_count')[:10],
        }

    @staticmethod
    def get_chart_data(days: int = 30) -> dict:
        end = date.today()
        start = end - timezone.timedelta(days=days)
        daily = DailyAnalytics.objects.filter(date__range=[start, end]).order_by('date')
        if not daily.exists():
            labels = [(start + timezone.timedelta(days=i)).isoformat() for i in range(days + 1)]
            return {'labels': labels, 'visitors': [0] * len(labels), 'page_views': [0] * len(labels)}
        return {
            'labels': [d.date.isoformat() for d in daily],
            'visitors': [d.unique_visitors for d in daily],
            'page_views': [d.page_views for d in daily],
        }
