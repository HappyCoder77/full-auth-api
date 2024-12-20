from .models import Edition
from promotions.utils import get_current_promotion


def get_current_editions():
    promotion = get_current_promotion()

    if promotion:
        return Edition.objects.filter(promotion=promotion)

    return Edition.objects.none()
