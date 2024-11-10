from dateutil import tz
from dateutil.relativedelta import relativedelta

from django.db import models, transaction
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone


User = get_user_model()


class Promotion(models.Model):
    """
    Representa una promoción con una date de inicio y fin.
    Una promoción es un período valido para participar en el llenado de una colección.
    Esta clase permite la inyección de un tiempo actual personalizado para
    facilitar las pruebas y la manipulación del tiempo en diferentes escenarios.

    Attributes:
        start_date (DateTimeField): La date y hora de inicio de la promoción.
        duration (PositiveSmallIntegerField): La duración de la promoción en días.
        end_date (DateTimeField): La date y hora de finalización de la promoción.
        pack_cost (DecimalField): El costo unitario del pack para esta promoción.
    """
    start_date = models.DateTimeField(
        "Date de Inicio", default=timezone.now, editable=False)
    duration = models.PositiveSmallIntegerField(
        'duración en días', default=1, )
    end_date = models.DateTimeField(
        "Date de finalización")
    pack_cost = models.DecimalField(verbose_name='costo unitario de pack',
                                    decimal_places=2,
                                    max_digits=4,
                                    default=0
                                    )

    def __init__(self, *args, **kwargs):
        """
        Inicializa una nueva instancia de Promotion.

        Args:
            *args: Argumentos posicionales para el modelo.
            **kwargs: Argumentos de palabra clave para el modelo.
                current_time (datetime, optional): Tiempo personalizado para usar
                    en cálculos de tiempo restante. Si no se proporciona, se usa
                    el tiempo actual del sistema.
        """
        self._current_time = kwargs.pop('current_time', None)
        super().__init__(*args, **kwargs)

    @property
    def current_time(self):
        """
        Devuelve el tiempo actual para cálculos de tiempo restante.

        Returns:
            datetime: El tiempo personalizado si se proporcionó, de lo contrario
                      el tiempo actual del sistema.
        """
        return self._current_time or timezone.now()

    def calculate_end_date(self):
        # Calcula la date de finalización basada en la duración
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
    def remaining_time(self):
        """
        Calcula y devuelve el tiempo restante de la promoción.

        Este método usa el tiempo actual (que puede ser personalizado) para
        calcular cuánto tiempo queda hasta que termine la promoción.

        Returns:
            str: Un mensaje describiendo el tiempo restante o indicando que
                 la promoción ha terminado.
        """
        now = self.current_time
        period = relativedelta(self.end_date, now)

        if self.end_date <= now:
            return "Esta promoción ha terminado."

        total_seconds = (self.end_date - now).total_seconds()

        if total_seconds < 86400:  # Menos de un día
            hours, remainder = divmod(int(total_seconds), 3600)
            minutes, seconds = divmod(remainder, 60)
            return f'Esta promoción termina en {hours} horas, {minutes} minutos y {seconds} segundos.'
        elif period.months < 1:
            return f'Esta promoción termina en {period.days} días y {period.hours} horas.'
        else:
            return f'Esta promoción termina en {period.months} meses y {period.days} días.'
        # if period.seconds < 0:
        #     mensaje = "Esta promoción ha terminado."
        # elif period.months < 1 and period.days < 1:
        #     mensaje = (
        #         f'Esta promoción termina en {period.hours} horas, {period.minutes} minutos y {period.seconds} segundos.')
        # elif period.months < 1:
        #     mensaje = (
        #         f'Esta promoción termina en {period.days} días y {period.hours} horas.')
        # else:
        #     mensaje = (
        #         f'Esta promoción termina en {period.months} meses y {period.days} días.')

        # return mensaje

    class Meta:
        verbose_name = "promotion"
        verbose_name_plural = "promotions"

    def clean(self):  # validacion de las dates de la promotion

        if self.pack_cost < 0:
            raise ValidationError(
                'El costo del pack no puede ser una cantidad negativa')
        # Validación de solapamiento de dates
        end_date = self.calculate_end_date()
        overlapping_promotions = self.__class__.objects.filter(
            models.Q(start_date__lt=end_date) & models.Q(
                end_date__gt=self.start_date)
        ).exclude(pk=self.pk)

        if overlapping_promotions.exists():
            raise ValidationError('Ya hay una promoción en curso')

    @transaction.atomic
    def save(self, *args, **kwargs):
        # self.reiniciar_rescue_options()
        date = self.calculate_end_date()
        date.replace(tzinfo=tz.gettz('America/Caracas'))
        # Nota: current_time no afecta el cálculo de end_date, solo se usa
        # para calcular el tiempo restante en el método remaining_time
        self.end_date = date
        super(Promotion, self).save(*args, **kwargs)
