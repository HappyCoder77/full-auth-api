from .models import Edition
from promotions.models import Promotion


def get_current_editions():
    promotion = Promotion.objects.get_current()

    if promotion:
        return Edition.objects.filter(promotion=promotion)

    return Edition.objects.none()
