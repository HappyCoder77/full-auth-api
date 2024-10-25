import datetime
import math
import random
from datetime import date
from dateutil import tz

from dateutil.relativedelta import relativedelta
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Count, Sum
from django.urls import reverse
from django.utils import timezone

User = get_user_model()


class Promotion(models.Model):  # periodo de tiempo válido para la venta de una colección
    start_date = models.DateTimeField(
        "Fecha de Inicio", default=timezone.now, editable=False)
    duration = models.PositiveSmallIntegerField(
        'duración en días', default=1, )
    end_date = models.DateTimeField("Fecha de finalización")
    envelope_cost = models.DecimalField(verbose_name='costo unitario de sobre',
                                        decimal_places=2,
                                        max_digits=4,
                                        default=0
                                        )

    def calculate_end_date(self):
        return self.start_date + relativedelta(days=self.duration)

    def translate_month(self, value):
        months = {
            'January': 'Enero',
            'February': 'Febrero',
            'March': 'Marzo',
            'April': 'Abril',
            'May': 'Mayo',
            'June': 'Junio',
            'July': 'Julio',
            'August': 'Agosto',
            'September': 'Septiembre',
            'October': 'Octubre',
            'November': 'Noviembre',
            'December': 'Diciembre'
        }
        return months.get(value, value)

    def __str__(self):

        start_year = self.start_date.strftime("%Y")
        start_month = self.translate_month(self.start_date.strftime("%B"))
        start_day = self.start_date.strftime("%d")
        end_year = self.end_date.strftime("%Y")
        end_month = self.translate_month(self.end_date.strftime("%B"))
        end_day = self.end_date.strftime("%d")
        start_full_date = f"{start_day} {start_month} {start_year}"
        end_full_date = f"{end_day} {end_month} {end_year}"

        return f"{start_full_date} / {end_full_date}"

    @property
    def remaining_time(self):  # Muestra mensaje con el tiempo restante de una promoción
        now = timezone.now()
        period = relativedelta(self.end_date, now)
        if period.months < 1 and period.days < 1:
            mensaje = (
                f'Esta promoción termina en {period.hours} horas, {period.minutes} minutos y {period.seconds} segundos.')
        elif period.months < 1:
            mensaje = (
                f'Esta promoción termina en {period.days} días y {period.hours} horas.')
        else:
            mensaje = (
                f'Esta promoción termina en {period.months} meses y {period.days} días')
        return mensaje

    class Meta:
        verbose_name = "promotion"
        verbose_name_plural = "promotions"

    def clean(self):  # validacion de las fechas de la promocion

        if self.envelope_cost < 0:
            raise ValidationError(
                'El costo del sobre no puede ser una cantidad negativa')
        # Validación de solapamiento de fechas
        end_date = self.calculate_end_date()
        overlapping_promotions = self.__class__.objects.filter(
            models.Q(start_date__lt=end_date) & models.Q(
                end_date__gt=self.start_date)
        ).exclude(pk=self.pk)

        if overlapping_promotions.exists():
            raise ValidationError('Ya hay una promocion en curso')

    # TODO:revisar si esto es viable aqui
    # def reiniciar_opciones_de_rescate(self):
    #     User.objects.filter(
    #         is_collector=True).update(opciones_de_rescate=0)

    @transaction.atomic
    def save(self, *args, **kwargs):
        # self.reiniciar_opciones_de_rescate()
        date = self.calculate_end_date()
        date.replace(tzinfo=tz.gettz('America/Caracas'))
        self.end_date = date
        super(Promotion, self).save(*args, **kwargs)
