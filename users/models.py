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

    objects = UserAccountManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


# TODO: add Address model


class BaseProfile(models.Model):
    # TODO: add address field
    # TODO: añadir validacion a la fecha de nacimiento para que usuarios distintos de coleccionistas deban ser mayores de edad
    user = models.OneToOneField(
        UserAccount, on_delete=models.CASCADE, null=True)
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, null=True, blank=True)
    first_last_name = models.CharField(max_length=50)
    second_last_name = models.CharField(max_length=50, null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENERO_CHOICES)
    birthdate = models.DateField(null=True, blank=True)
    email = models.EmailField(_("Email field"), unique=True)


class RegionalManager(BaseProfile):
    created_by = models.ForeignKey(
        UserAccount, on_delete=models.SET_NULL, null=True, related_name='created_profiles')

    def __str__(self) -> str:
        return self.first_name + " " + self.first_last_name
