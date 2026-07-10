"""Celery tasks for notifications."""
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from news.models import Article
from notifications.models import Notification
from accounts.models import User


@shared_task
def send_breaking_news_alert(article_id: int):
    try:
        article = Article.objects.get(pk=article_id)
    except Article.DoesNotExist:
        return
    users = User.objects.filter(newsletter_subscribed=True, is_active=True)
    for user in users[:1000]:
        Notification.objects.create(
            user=user,
            notification_type='breaking_news',
            title=f'Breaking: {article.title}',
            message=article.excerpt[:200],
            link=article.get_absolute_url(),
        )
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f'user_{user.id}',
                {'type': 'send_notification', 'data': {'title': article.title, 'url': article.get_absolute_url()}},
            )
