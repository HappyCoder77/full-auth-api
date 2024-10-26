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


class Promotion(models.Model):
    """
    Representa una promoción con una fecha de inicio y fin.
    Una promoción es un período valido para participar en el llenado de una colección.
    Esta clase permite la inyección de un tiempo actual personalizado para
    facilitar las pruebas y la manipulación del tiempo en diferentes escenarios.

    Attributes:
        start_date (DateTimeField): La fecha y hora de inicio de la promoción.
        duration (PositiveSmallIntegerField): La duración de la promoción en días.
        end_date (DateTimeField): La fecha y hora de finalización de la promoción.
        envelope_cost (DecimalField): El costo unitario del sobre para esta promoción.
    """
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
        # Calcula la fecha de finalización basada en la duración
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

        if period.seconds < 0:
            mensaje = "Esta promoción ha terminado."
        elif period.months < 1 and period.days < 1:
            mensaje = (
                f'Esta promoción termina en {period.hours} horas, {period.minutes} minutos y {period.seconds} segundos.')
        elif period.months < 1:
            mensaje = (
                f'Esta promoción termina en {period.days} días y {period.hours} horas.')
        else:
            mensaje = (
                f'Esta promoción termina en {period.months} meses y {period.days} días.')

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
        # Nota: current_time no afecta el cálculo de end_date, solo se usa
        # para calcular el tiempo restante en el método remaining_time
        self.end_date = date
        super(Promotion, self).save(*args, **kwargs)


class Collection(models.Model):
    PAGES = 4
    SLOTS_PER_PAGE = 6
    STICKERS_PER_PACK = 3
    PACKS_PER_BOX = 100
    PRIZE_STICKER_COORDINATE = 99
    SURPRISE_PRIZE_OPTIONS = 4
    RARITY_1 = 3
    RARITY_2 = 2
    RARITY_3 = 1
    RARITY_4 = 1  # 0.02
    RARITY_5 = 1  # 0.01
    RARITY_6 = 1  # 0.006
    RARITY_7 = 1  # 0.004
    PRIZE_STICKER_RARITY = float(0.301)
    name = models.CharField("Tema de la colección",
                            max_length=50, unique=True)
    image = models.ImageField(upload_to='albums', null=True)

    def __str__(self):
        return self.name

    # def get_absolute_url(self):
    #     return reverse('Collection_detail', kwargs={'pk': self.pk})

    class Meta:
        verbose_name = "colección"
        verbose_name_plural = "Colecciones"

    @transaction.atomic
    def save(self, *args, **kwargs):
        super(Collection, self).save(*args, **kwargs)
        self.create_coordinates()
        self.shuffle_coordinates()
        self.distribute_rarity()
        self.create_standard_prizes()
        self.create_surprise_prizes()

    def create_coordinates(self):  # función que crea las coordinates de una colección
        coordinates_list = []
        counter = 1
        current_page = 1

        while current_page <= self.PAGES:  # bucle que recorre las pages del album
            current_slot = 1

            while current_slot <= self.SLOTS_PER_PAGE:  # bucle que recorre las barajitas de cada page,
                # y crea las coordinates correspondientes
                coordinate = Coordinate(
                    collection=self,
                    page=current_page,
                    slot=current_slot,
                    ordinal=current_slot,
                    number=counter,
                    rarity_factor=0
                )

                coordinates_list.append(coordinate)
                current_slot += 1
                counter += 1

            current_page += 1

        coordinate = Coordinate(  # creacion de las coordinates de la barajita premiada
            collection=self,
            page=self.PRIZE_STICKER_COORDINATE,
            slot=self.PRIZE_STICKER_COORDINATE,
            rarity_factor=float(self.PRIZE_STICKER_RARITY)
        )

        coordinates_list.append(coordinate)
        Coordinate.objects.bulk_create(coordinates_list)

    # función que desordena el atributo slot de las coordinates
    def shuffle_coordinates(self):
        coordinates_list = []
        current_page = 1

        # bucle que itera sobre cada page del álbum
        while current_page <= self.PAGES:
            list = []
            counter = 1

        # bucle que itera sobre cada cada barajita del la página en curso
        # y llena la lista con range_options igual al número de coordinates por page
            while counter <= self.SLOTS_PER_PAGE:
                list.append(counter)
                counter += 1

            random.shuffle(list)  # desordena la ista obtenida
            counter = 0

            # edito la propiedad ordinal para generar el desordenamiento de las coordinates por cada página
            for each_coordinate in self.coordinates.filter(page=current_page):
                each_coordinate.ordinal = list[counter]
                coordinates_list.append(each_coordinate)
                counter += 1

            current_page += 1

        Coordinate.objects.bulk_update(coordinates_list, ['ordinal'])

    # funcion que asigna los factores de rareza a las coordinates
    def distribute_rarity(self):
        coordinates_list = []
        # asigno los factores de rareza comun en función del número de barajita
        for each_coordinate in self.coordinates.all():
            if each_coordinate.slot == 1 or each_coordinate.slot == 2:
                each_coordinate.factor_de_rareza = self.RARITY_1
            elif each_coordinate.slot == 3 or each_coordinate.slot == 4:
                each_coordinate.factor_de_rareza = self.RARITY_2
            elif each_coordinate.slot == 5:
                each_coordinate.factor_de_rareza = self.RARITY_3
            elif each_coordinate.slot == 6:  # asigno los factores de rareza mas elevados a una unica barajita por página

                if each_coordinate.page == 1:
                    each_coordinate.factor_de_rareza = self.RARITY_4
                if each_coordinate.page == 2:
                    each_coordinate.factor_de_rareza = self.RARITY_5
                if each_coordinate.page == 3:
                    each_coordinate.factor_de_rareza = self.RARITY_6
                if each_coordinate.page == 4:
                    each_coordinate.factor_de_rareza = self.RARITY_7

            coordinates_list.append(each_coordinate)

        Coordinate.objects.bulk_update(coordinates_list, ['rarity_factor'])

    def create_standard_prizes(self):
        pages = range(1, self.PAGES + 1)

        for page in pages:
            StandardPrize.objects.create(
                collection_id=self.id, description='descripción de premio standard', page=page)

    def create_surprise_prizes(self):
        range_options = range(1, self.SURPRISE_PRIZE_OPTIONS + 1)

        for counter in range_options:
            SurprisePrize.objects.create(
                collection_id=self.id, description='descripción de premio sorpresa', number=counter)


class Coordinate(models.Model):
    collection = models.ForeignKey(
        Collection, on_delete=models.CASCADE, related_name='coordinates')
    page = models.BigIntegerField('Número de página')
    slot = models.BigIntegerField('Número de barajita')
    ordinal = models.BigIntegerField('number ordinal por página', default=0)
    number = models.BigIntegerField('Número en album', default=0)
    rarity_factor = models.DecimalField(
        'Factor de rareza', max_digits=6, decimal_places=3)

    def __str__(self):
        return str(self.number)

    class Meta:
        verbose_name_plural = "Coordinates"


class SurprisePrize(models.Model):
    collection = models.ForeignKey(
        Collection, on_delete=models.CASCADE, null=True, related_name='surprise_prizes')
    number = models.SmallIntegerField(default=0)
    description = models.CharField(max_length=100)

    def __str__(self):
        return self.description

    class Meta:
        verbose_name = 'premio_sorpresa'
        verbose_name_plural = 'premios sorpresa'


class StandardPrize(models.Model):
    collection = models.ForeignKey(
        Collection, on_delete=models.CASCADE, null=True, related_name='standard_prizes')
    page = models.SmallIntegerField()
    description = models.CharField(max_length=100)

    def __str__(self):
        return self.description

    class Meta:
        verbose_name_plural = 'premios standard'
