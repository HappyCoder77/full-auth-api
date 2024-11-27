from django.utils import timezone
from .models import Promotion


def promotion_is_running():
    now = timezone.now()
    return Promotion.objects.filter(
        start_date__lte=now,
        end_date__gte=now
    ).exists()
