from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser, PermissionsMixin)
from django.utils.translation import gettext_lazy as _


GENERO_CHOICES = [
    ("M", "Masculino"),
    ("F", "Femenino")
]


class UserAccountManager(BaseUserManager):
    def create_user(self, email, password=None, **kwargs):

        if not email:
            raise ValueError(
                "Para crear un usario se debe proporcionar una dirección de correo electrónico")

        if not password:
            raise ValueError('La contraseña no puede estar vacía')

        email = self.normalize_email(email)
        email = email.lower()

        user = self.model(
            email=email,
            **kwargs
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **kwargs):
        user = self.create_user(
            email,
            password=password,
            **kwargs
        )
        user.is_staff = True
        user.is_superuser = True

        user.save(using=self._db)
        return user


class UserAccount(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=255, unique=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_collector = models.BooleanField(default=False)

    objects = UserAccountManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    def is_regionalmanager(self):
        return hasattr(self, 'baseprofile') and hasattr(self.baseprofile, 'regionalmanager')

    def is_localmanager(self):
        return hasattr(self, 'baseprofile') and hasattr(self.baseprofile, 'localmanager')

    def is_sponsor(self):
        return hasattr(self, 'baseprofile') and hasattr(self.baseprofile, 'sponsor')

    def is_dealer(self):
        return hasattr(self, 'baseprofile') and hasattr(self.baseprofile, 'dealer')

# TODO: add Address model
# TODO: add region Model
# TODO: add locality model


class BaseProfile(models.Model):
    # TODO: add address field
    # TODO: añadir validacion a la fecha de nacimiento para que usuarios distintos de coleccionistas deban ser mayores de edad
    user = models.OneToOneField(
        UserAccount, on_delete=models.CASCADE, null=True)
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50)
    second_last_name = models.CharField(max_length=50, null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENERO_CHOICES)
    birthdate = models.DateField(null=True, blank=True)
    email = models.EmailField(_("Email field"), unique=True)

# TODO: refactor __str__ method in baseprofile


class RegionalManager(BaseProfile):
    created_by = models.ForeignKey(
        UserAccount, on_delete=models.SET_NULL, null=True, related_name='created_regionalmanagers')

    def __str__(self) -> str:
        return self.first_name + " " + self.last_name


class LocalManager(BaseProfile):
    created_by = models.ForeignKey(
        UserAccount, on_delete=models.SET_NULL, null=True, related_name='created_localmanagers')

    def __str__(self) -> str:
        return self.first_name + " " + self.last_name


class Sponsor(BaseProfile):
    created_by = models.ForeignKey(
        UserAccount, on_delete=models.SET_NULL, null=True, related_name='created_sponsors')

    def __str__(self) -> str:
        return self.first_name + " " + self.last_name


class Dealer(BaseProfile):
    created_by = models.ForeignKey(
        UserAccount, on_delete=models.SET_NULL, null=True, related_name='created_dealers')

    def __str__(self) -> str:
        return self.first_name + " " + self.last_name
