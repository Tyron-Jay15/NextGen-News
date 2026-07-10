"""Advertisement services."""
from django.db.models import F
from django.utils import timezone

from advertisements.models import AdClick, AdImpression, Advertisement
from config.utils import get_client_ip


class AdService:
    @staticmethod
    def get_ads_for_placement(placement: str, limit: int = 3):
        now = timezone.now()
        return Advertisement.objects.filter(
            placement=placement,
            is_active=True,
            start_date__lte=now,
            end_date__gte=now,
        ).order_by('-priority')[:limit]

    @staticmethod
    def record_impression(request, ad_id: int):
        Advertisement.objects.filter(pk=ad_id).update(impression_count=F('impression_count') + 1)
        AdImpression.objects.create(
            advertisement_id=ad_id,
            ip_address=get_client_ip(request),
            page_url=request.path,
        )

    @staticmethod
    def record_click(request, ad_id: int):
        Advertisement.objects.filter(pk=ad_id).update(click_count=F('click_count') + 1)
        AdClick.objects.create(
            advertisement_id=ad_id,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
        )
