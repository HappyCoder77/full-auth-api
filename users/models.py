from django.db import models
from django.utils.translation import gettext_lazy as _

from authentication.models import UserAccount

GENERO_CHOICES = [
    ("M", "Masculino"),
    ("F", "Femenino")
]


class BaseProfile(models.Model):
    # TODO: add address field
    # TODO: añadir validacion a la fecha de nacimiento para que usuarios distintos de coleccionistas deban ser mayores de edad
    user = models.OneToOneField(
        UserAccount, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50)
    second_last_name = models.CharField(max_length=50, null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENERO_CHOICES)
    # TODO: este campo no deberia ser opcional
    birthdate = models.DateField(null=True, blank=True)
    email = models.EmailField(_("Email field"), unique=True)

    def __str__(self) -> str:
        return self.first_name + " " + self.last_name


class RegionalManager(BaseProfile):
    created_by = models.ForeignKey(
        UserAccount, on_delete=models.SET_NULL, null=True, related_name='created_regionalmanagers')


class LocalManager(BaseProfile):
    created_by = models.ForeignKey(
        UserAccount, on_delete=models.SET_NULL, null=True, related_name='created_localmanagers')


class Sponsor(BaseProfile):
    created_by = models.ForeignKey(
        UserAccount, on_delete=models.SET_NULL, null=True, related_name='created_sponsors')


class Dealer(BaseProfile):
    created_by = models.ForeignKey(
        UserAccount, on_delete=models.SET_NULL, null=True, related_name='created_dealers')
