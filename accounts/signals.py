"""Account signals."""
from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import User, UserProfile
from notifications.models import NotificationPreference


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
        NotificationPreference.objects.get_or_create(user=instance)
