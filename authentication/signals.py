from datetime import date, timedelta
from django.apps import apps
from django.db.models.signals import post_save
from django.dispatch import receiver
from promotions.utils import get_current_promotion, get_last_promotion
from commerce.models import DealerBalance
from .models import UserAccount


@receiver(post_save, sender=UserAccount)
def handle_user_post_save(sender, instance, created, **kwargs):

    if not created or instance.is_superuser:
        return

    link_user_to_profile(instance)

    if instance.is_dealer:
        create_balance_for_new_dealer(instance)


def link_user_to_profile(user):
    profile_models = [
        "RegionalManager",
        "LocalManager",
        "Sponsor",
        "Dealer",
        "Collector",
    ]

    for model_name in profile_models:
        ProfileModel = apps.get_model("users", model_name)

        try:
            profile = ProfileModel.objects.get(email=user.email, user__isnull=True)
            profile.user = user
            profile.save()
            return
        except ProfileModel.DoesNotExist:
            continue


def create_balance_for_new_dealer(user):
    last_promotion = get_last_promotion()
    current_promotion = get_current_promotion()
    start_date = (
        (last_promotion.end_date + timedelta(days=1))
        if last_promotion
        else date.today()
    )

    if current_promotion:
        # Si hay promoción activa, crear balance con promoción
        DealerBalance.objects.create(
            dealer=user, promotion=current_promotion, start_date=start_date
        )
    else:
        # Si no hay promoción activa, crear balance sin promoción
        DealerBalance.objects.create(dealer=user, start_date=start_date)
