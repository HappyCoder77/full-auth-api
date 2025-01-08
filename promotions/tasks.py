from celery import shared_task
import logging
from django.utils import timezone
from .models import Promotion

logger = logging.getLogger(__name__)


@shared_task
def check_ended_promotions():
    print("------------------check_ended_promotions")
    logger.info("Ejecutando tarea para verificar promociones finalizadas")
    today = timezone.now().date()
    logger.info(f"Today's date: {today}")

    ended_promotions = Promotion.objects.filter(
        end_date__date__lte=today,
        balances_created=False,
    )
    logger.info(f"ended_promotions: {ended_promotions}")
    logger.info(f"Found {ended_promotions.count()} ended promotions")

    for promotion in ended_promotions:
        try:
            logger.info(f"Updating promotion: {promotion.id}")
            promotion.balances_created = True
            promotion.save()
            logger.info(f"Promotion {promotion.id} updated")
        except Exception as e:
            logger.error(f"Error updating promotion {promotion.id}: {str(e)}")
