from django.apps import apps
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserAccount


@receiver(post_save, sender=UserAccount)
def link_profile(sender, instance, created, **kwargs):

    if created:
        link_user_to_profile(instance)


def link_user_to_profile(user):
    profile_models = ["RegionalManager", "LocalManager"]

    for model_name in profile_models:
        ProfileModel = apps.get_model("users", model_name)

        try:
            profile = ProfileModel.objects.get(
                email=user.email, user__isnull=True)
            profile.user = user
            profile.save()
            return
        except ProfileModel.DoesNotExist:

            try:
                user.is_collector = True
                user.save()
            except Exception as e:
                print(f"Error al marcar al usuario como coleccionista: {e}")
