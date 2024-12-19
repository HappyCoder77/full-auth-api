from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Promotion
from commerce.models import DealerBalance


@receiver(post_save, sender=Promotion)
def assign_promotion_to_open_balances(sender, instance, created, **kwargs):
    if created:
        # Asignar la nueva promoción a balances sin promoción
        open_balances = DealerBalance.objects.filter(promotion__isnull=True)

        for balance in open_balances:
            balance.promotion = instance
            balance.save()
