from datetime import date, timedelta
from django.apps import apps
from django.db.models.signals import post_save
from django.dispatch import receiver
from promotions.utils import get_current_promotion, get_last_promotion
from commerce.models import DealerBalance
from .models import UserAccount


@receiver(post_save, sender=UserAccount)
def handle_user_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for the post-save event of a User model.

    This function is triggered after a User instance is saved. It performs the following actions:
    - If the User instance is newly created and is not a superuser, it links the user to a profile.
    - If the User instance is a dealer, it creates a balance for the new dealer.

    Args:
        sender (type): The model class that sent the signal.
        instance (User): The actual instance being saved.
        created (bool): A boolean indicating whether a new record was created.
        **kwargs: Additional keyword arguments.
    """

    if not created or instance.is_superuser:
        return

    link_user_to_profile(instance)

    if instance.is_dealer:
        create_balance_for_new_dealer(instance)


def link_user_to_profile(user):
    """
    Links a user to their corresponding profile if it exists.

    This function iterates through a list of profile models and attempts to find
    a profile with the same email as the user and where the user field is null.
    If such a profile is found, it assigns the user to the profile and saves it.

    Args:
        user (User): The user instance to link to a profile.

    Raises:
        ProfileModel.DoesNotExist: If no matching profile is found for the user.
    """
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
    """
    Creates a balance entry for a new dealer.

    This function checks for the last and current promotions and creates a
    DealerBalance entry for the given user. If there is a current promotion,
    the balance is created with the promotion details. If there is no current
    promotion, the balance is created without promotion details.
    If there is no last promotion, the balance is created with the current date,
    otherwise it is created with the day after the last promotion ended.

    Args:
        user: The user object representing the dealer for whom the balance
              is being created.

    Returns:
        None
    """
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
