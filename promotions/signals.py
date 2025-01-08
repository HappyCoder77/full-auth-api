from datetime import timedelta
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Promotion
from commerce.models import DealerBalance
from users.models import Dealer  # Import the Dealer model directly


@receiver(post_save, sender=Promotion)
def handle_promotion_ending(sender, instance, created, **kwargs):
    """
    Signal handler for the Promotion model.

    This function handles the post_save signal for the Promotion model. It performs
    different actions based on whether the promotion instance was created or updated.

    If a new promotion is created:
    - It assigns the new promotion to all DealerBalance instances that do not have a promotion.

    If an existing promotion is updated:
    - It checks if the promotion has ended.
    - If the promotion has ended and there are no open balances for the dealers, it creates a new balance for each dealer.
    - The start date of the balnce depends on the existence or not of aprevious balance.

    Args:
        sender (Model): The model class that sent the signal.
        instance (Promotion): The instance of the Promotion model that triggered the signal.
        created (bool): A boolean indicating whether a new record was created.
        **kwargs: Additional keyword arguments.
    """

    if created:
        open_balances = DealerBalance.objects.filter(promotion__isnull=True)

        for balance in open_balances:
            balance.promotion = instance
            balance.save()
    else:

        if instance.end_date.date() < timezone.now().date():
            dealers = Dealer.objects.all()

            for dealer in dealers:
                print("dealer: ", dealer.user)
                last_balance = DealerBalance.objects.filter(
                    dealer=dealer.user, promotion=instance
                ).first()
                print("last balance: ", last_balance)
                open_balance = DealerBalance.objects.filter(
                    dealer=dealer.user,
                    promotion=None,
                    start_date=instance.end_date.date() + timedelta(days=1),
                ).first()
                print(open_balance)
                if not open_balance:
                    DealerBalance.objects.create(
                        dealer=dealer.user,
                        promotion=None,
                        initial_balance=(
                            last_balance.current_balance
                            if last_balance and last_balance.current_balance is not None
                            else 0
                        ),
                        start_date=instance.end_date.date() + timedelta(days=1),
                    )
