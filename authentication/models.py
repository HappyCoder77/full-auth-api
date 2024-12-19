from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

from django.db import models

from .managers import UserAccountManager


class UserAccount(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=255, unique=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UserAccountManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    @property
    def is_regionalmanager(self):
        return hasattr(self, "baseprofile") and hasattr(
            self.baseprofile, "regionalmanager"
        )

    @property
    def is_localmanager(self):
        return hasattr(self, "baseprofile") and hasattr(
            self.baseprofile, "localmanager"
        )

    @property
    def is_sponsor(self):
        return hasattr(self, "baseprofile") and hasattr(self.baseprofile, "sponsor")

    @property
    def is_dealer(self):
        return hasattr(self, "baseprofile") and hasattr(self.baseprofile, "dealer")

    @property
    def is_collector(self):
        return self.has_profile and hasattr(self.baseprofile, "collector")

    @property
    def has_profile(self):
        return hasattr(self, "baseprofile")


# TODO: add Address model
# TODO: add region Model
# TODO: add locality model
