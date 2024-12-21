from datetime import timedelta
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Promotion
from commerce.models import DealerBalance
from users.models import Dealer  # Import the Dealer model directly


@receiver(post_save, sender=Promotion)
def handle_promotion_signals(sender, instance, created, **kwargs):
    if created:
        # Assign the new promotion to balances without promotion
        open_balances = DealerBalance.objects.filter(promotion__isnull=True)

        for balance in open_balances:
            balance.promotion = instance
            balance.save()
    else:
        # Check if this promotion has already ended
        if instance.end_date.date() < timezone.now().date():
            # Query the Dealer table directly
            dealers = Dealer.objects.all()

            for dealer in dealers:
                last_balance = DealerBalance.objects.filter(
                    dealer=dealer.user, promotion=instance
                ).first()

                # Create new balance period starting right after promotion ends
                DealerBalance.objects.create(
                    dealer=dealer.user,
                    promotion=None,  # No promotion assigned yet
                    initial_balance=(
                        last_balance.current_balance
                        if last_balance and last_balance.current_balance is not None
                        else 0
                    ),
                    start_date=instance.end_date.date() + timedelta(days=1),
                )
