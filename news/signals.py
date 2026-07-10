"""News signals."""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils.text import slugify

from news.models import Article


@receiver(pre_save, sender=Article)
def article_pre_save(sender, instance, **kwargs):
    if not instance.slug:
        instance.slug = slugify(instance.title)[:300]


@receiver(post_save, sender=Article)
def article_post_save(sender, instance, created, **kwargs):
    if instance.status == 'published' and instance.is_breaking:
        from notifications.tasks import send_breaking_news_alert
        send_breaking_news_alert.delay(instance.pk)
