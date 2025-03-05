from django.utils import timezone
from .models import Promotion


# TODO: eliminar este archivo. fue mudado al manager
def promotion_is_running():
    now = timezone.now()
    return Promotion.objects.filter(start_date__lte=now, end_date__gte=now).exists()


def get_current_promotion():
    now = timezone.now()

    try:
        return Promotion.objects.get(start_date__lte=now, end_date__gte=now)
    except Promotion.DoesNotExist:  # pragma: no cover
        return None


def get_last_promotion():
    now = timezone.now()

    try:
        return Promotion.objects.filter(end_date__lt=now).order_by("-end_date").first()
    except Promotion.DoesNotExist:
        return None
