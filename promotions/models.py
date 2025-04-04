from dateutil import tz
from dateutil.relativedelta import relativedelta
from datetime import timedelta, date

from django.db import models, transaction
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Manager
from django.utils import timezone


User = get_user_model()


class PromotionManager(Manager):
    def is_running(self):
        today = timezone.localtime(timezone.now()).date()
        return Promotion.objects.filter(
            start_date__lte=today, end_date__gte=today
        ).exists()

    def get_current(self):
        today = timezone.localtime(timezone.now()).date()

        try:
            return Promotion.objects.get(start_date__lte=today, end_date__gte=today)
        except Promotion.DoesNotExist:  # pragma: no cover
            return None

    def get_last(self):
        today = timezone.localtime(timezone.now()).date()

        try:
            return (
                Promotion.objects.filter(end_date__lt=today)
                .order_by("-end_date")
                .first()
            )
        except Promotion.DoesNotExist:
            return None


class Promotion(models.Model):
    """
    Representa una promoción con una fecha de inicio y fin.
    Una promoción es un período valido para participar en el llenado de una colección.

    Attributes:
        start_date (DateField): La fecha de inicio de la promoción.
        duration (PositiveSmallIntegerField): La duración de la promoción en días.
        end_date (DateField): La fecha de finalización de la promoción.
        pack_cost (DecimalField): El costo unitario del pack para esta promoción.
    """

    objects = PromotionManager()
    start_date = models.DateField("Fecha de Inicio", default=date.today, editable=False)
    duration = models.PositiveSmallIntegerField(
        "duración en días",
        default=1,
    )
    end_date = models.DateField("Fecha de finalización", null=True, blank=True)
    pack_cost = models.DecimalField(
        verbose_name="costo unitario de pack", decimal_places=2, max_digits=4, default=0
    )

    balances_created = models.BooleanField(default=False)

    def calculate_end_date(self):
        # Calcula la date de finalización basada en la duración
        return self.start_date + timedelta(days=self.duration - 1)

    def __str__(self):
        start_year = self.start_date.strftime("%Y")
        start_month = self.translate_month(self.start_date.strftime("%B"))
        start_day = self.start_date.strftime("%d")
        end_year = self.end_date.strftime("%Y")
        end_month = self.translate_month(self.end_date.strftime("%B"))
        end_day = self.end_date.strftime("%d")
        start_full_date = f"{start_day} {start_month} {start_year}"
        end_full_date = f"{end_day} {end_month} {end_year}"

        return f"del {start_full_date} al {end_full_date}"

    @transaction.atomic
    def save(self, *args, **kwargs):
        self.end_date = self.calculate_end_date()
        super(Promotion, self).save(*args, **kwargs)

    def translate_month(self, value):
        months = {
            "January": "Enero",
            "February": "Febrero",
            "March": "Marzo",
            "April": "Abril",
            "May": "Mayo",
            "June": "Junio",
            "July": "Julio",
            "August": "Agosto",
            "September": "Septiembre",
            "October": "Octubre",
            "November": "Noviembre",
            "December": "Diciembre",
        }
        return months.get(value, value)

    @property
    def remaining_time(self):
        today = timezone.localtime(timezone.now()).date()

        if self.end_date < today:
            return "Esta promoción ha terminado."

        period = relativedelta(self.end_date, today)

        if self.end_date == today:
            return "Esta promoción termina hoy a la medianoche."

        elif period.months < 1:
            days_remaining = (self.end_date - today).days + 1
            return f"Esta promoción termina en {days_remaining} días."
        else:
            return (
                f"Esta promoción termina en {period.months} meses y {period.days} días."
            )

    @property
    def max_debt(self):
        """
        Calculate the maximum debt for the promotion based on the cost of the editions.

        Returns:
            float: The average cost of the editions if there are any, otherwise 0.
        """
        try:
            collections = self.collections.all()
        except models.ObjectDoesNotExist:
            return 0

        debt = 0

        for collection in collections:
            debt += collection.box_cost

        if collections.count() > 0:
            debt = debt / collections.count()
        else:
            debt = 0

        return debt

    class Meta:
        verbose_name = "promotion"
        verbose_name_plural = "promotions"

    def clean(self):
        unclose_promotions = self.__class__.objects.filter(
            balances_created=False
        ).exclude(pk=self.pk)

        if unclose_promotions.exists():
            raise ValidationError(
                "Hay promociones sin cerrar, no se puede crear una nueva promoción."
            )
        if self.pack_cost < 0:
            raise ValidationError(
                "El costo del pack no puede ser una cantidad negativa"
            )
        # Validación de solapamiento de dates
        end_date = self.calculate_end_date()
        overlapping_promotions = self.__class__.objects.filter(
            models.Q(start_date__lte=end_date) & models.Q(end_date__gte=self.start_date)
        ).exclude(pk=self.pk)

        if overlapping_promotions.exists():
            raise ValidationError("Ya hay una promoción en curso")
