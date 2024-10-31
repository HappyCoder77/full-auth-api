import math
import random
from decimal import Decimal, getcontext, ROUND_CEILING, ROUND_DOWN
from dateutil import tz

from dateutil.relativedelta import relativedelta
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Count
from django.urls import reverse
from django.utils import timezone

getcontext().prec = 6
User = get_user_model()
"""TODO: Explorar una mecanica de creacion mas eficiente y menos propensa a errores.
Podria ser creando pack y boxes
sobre la marcha,consolidando el atributo edition en un solo lugar, 
Se podria crear un clase diagramado o algo asi para contener la configuracion del album
crear rama para este trabajo exclusivamente"""


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
    end_date = models.DateTimeField("Date de finalización")
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

    # TODO:revisar si esto es viable aqui
    # def reiniciar_rescue_options(self):
    #     User.objects.filter(
    #         is_collector=True).update(rescue_options=0)

    @transaction.atomic
    def save(self, *args, **kwargs):
        # self.reiniciar_rescue_options()
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
    RARITY_1 = Decimal(3)
    RARITY_2 = Decimal(2)
    RARITY_3 = Decimal(1)
    RARITY_4 = Decimal(0.02).quantize(Decimal('0.00'))
    RARITY_5 = Decimal(0.01).quantize(Decimal('0.00'))
    RARITY_6 = Decimal(0.006).quantize(Decimal('0.000'))
    RARITY_7 = Decimal(0.004).quantize(Decimal('0.000'))
    PRIZE_STICKER_RARITY = Decimal(0.301).quantize(Decimal('0.000'))
    name = models.CharField("Tema de la colección",
                            max_length=50, unique=True)
    image = models.ImageField(upload_to='albums', null=True)

    def __str__(self):
        return self.name

    # def get_absolute_url(self):
    #     return reverse('Collection_detail', kwargs={'pk': self.pk})

    class Meta:
        verbose_name = "collection"
        verbose_name_plural = "collections"

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

            while current_slot <= self.SLOTS_PER_PAGE:  # bucle que recorre las stickers de cada page,
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

        coordinate = Coordinate(  # creacion de las coordinates de la sticker premiada
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

        # bucle que itera pack cada page del álbum
        while current_page <= self.PAGES:
            list = []
            counter = 1

        # bucle que itera pack cada cada sticker del la página en curso
        # y llena la list con range_options igual al número de coordinates por page
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

    # funcion que asigna los factores de rarity a las coordinates
    def distribute_rarity(self):

        coordinates_list = []
        # asigno los factores de rarity comun en función del número de sticker
        for each_coordinate in self.coordinates.all():

            if each_coordinate.slot == 1 or each_coordinate.slot == 2:
                each_coordinate.rarity_factor = self.RARITY_1
            elif each_coordinate.slot == 3 or each_coordinate.slot == 4:
                each_coordinate.rarity_factor = self.RARITY_2
            elif each_coordinate.slot == 5:
                each_coordinate.rarity_factor = self.RARITY_3
            elif each_coordinate.slot == 6:  # asigno los factores de rarity mas elevados a una unica sticker por página

                if each_coordinate.page == 1:
                    each_coordinate.rarity_factor = self.RARITY_4
                if each_coordinate.page == 2:
                    each_coordinate.rarity_factor = self.RARITY_5
                if each_coordinate.page == 3:
                    each_coordinate.rarity_factor = self.RARITY_6
                if each_coordinate.page == 4:
                    each_coordinate.rarity_factor = self.RARITY_7

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
    slot = models.BigIntegerField('Número de sticker')
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
        verbose_name = 'surprise prize'
        verbose_name_plural = 'surprise prizes'


class StandardPrize(models.Model):
    collection = models.ForeignKey(
        Collection, on_delete=models.CASCADE, null=True, related_name='standard_prizes')
    page = models.SmallIntegerField()
    description = models.CharField(max_length=100)

    def __str__(self):
        return self.description

    class Meta:
        verbose_name_plural = 'standard prizes'


class Edition(models.Model):  # clase para crear las editiones que se haran en cada promoción
    # TODO: este campo deberia null True porque se establece a traves del metodo clean
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    circulation = models.DecimalField(
        max_digits=20, decimal_places=0, default=Decimal('1'))

    class Meta:
        verbose_name = "Edition"
        verbose_name_plural = "Editions"

    def __str__(self):
        return self.collection.name

    def clean(self):
        try:  # verifica que exista una promotion
            last_promotion = Promotion.objects.latest(
                'end_date')
        except Promotion.DoesNotExist:
            last_promotion = None
        # valida la creación del registro dependiendo de si existe o no una promoción
        # anterior o, en caso de existir, que la misma no haya terminado

        if last_promotion == None or last_promotion.end_date < timezone.now():
            raise ValidationError(
                '''No hay ninguna promoción en curso. 
            Por lo tanto, debe crearla primero y luego
            intentar de nuevo agregar este registro'''
            )
        else:
            try:  # verifica que no exista otra collection con el mismo name
                collection = self.__class__.objects.get(
                    collection=self.collection, promotion=last_promotion)
            except self.__class__.DoesNotExist:
                collection = None

            if collection != None:
                raise ValidationError(
                    '''Ya existe una edición con la misma colección;
                    quiza deberia considerar realizar una reedición.'''
                )
            else:
                standard_prize = self.collection.standard_prizes.first()
                if standard_prize.description == 'descripción de premio standard':
                    raise ValidationError(
                        '''La edición a la que se hace referencia parece no tener definidos los premios 
                        standard. Revise e intente de nuevo guardar el registro''')

                surprise_prize = self.collection.surprise_prizes.first()

                if surprise_prize.description == 'descripción de premio sorpresa':
                    raise ValidationError(
                        '''La edición a la que se hace referencia parece no tener definidos los prizes 
                        sorpresa. Revise e intente de nuevo guardar el registro''')

            self.promotion = last_promotion

    @transaction.atomic
    def save(self, *args, **kwargs):
        super(Edition, self).save(*args, **kwargs)
        # start = time.time()
        self.create_stickers()
        self.shuffle_stickers()
        self.create_packs()
        self.fill_packs()
        self.shuffle_packs()
        self.create_boxes()
        self.fill_boxes()
        self.shuffle_boxes()
        # end = time.time()
        # duracion = end - start
        # ('duracion metodo save:', duracion)

    # crea la quantity estipulada de stickers segun en el circulation de cada sticker
    def create_stickers(self):
        sticker_list = []
        ordinal = 1  # hace un conteo general de los stickers
        limit = 0
        prize_rarity = self.collection.PRIZE_STICKER_RARITY

        for each_coordinate in self.collection.coordinates.all():
            circulation_counter = 1

            # asigna el limit de circulation, dependiendo de si
            # es una barajia premiada o no
            if each_coordinate.rarity_factor == prize_rarity:
                limit = (each_coordinate.rarity_factor *
                         self.circulation).quantize(Decimal('1'), rounding=ROUND_CEILING)
            else:
                limit = (each_coordinate.rarity_factor *
                         self.circulation).quantize(Decimal('1'), rounding=ROUND_DOWN)

            sticker_list = []

            while circulation_counter <= limit:
                sticker = Sticker(
                    coordinate=each_coordinate,
                    ordinal=ordinal
                )

                sticker_list.append(sticker)

                if len(sticker_list) >= 500:
                    Sticker.objects.bulk_create(sticker_list)
                    sticker_list = []
                circulation_counter += 1
                ordinal += 1

            Sticker.objects.bulk_create(sticker_list)

    # aplica orden aleatorio a los valores del atributo ordinal de los stickers

    def shuffle_stickers(self):
        stickers = Sticker.objects.filter(pack__isnull=True).only('ordinal')
        list = []
        counter = 1

        # llena la list con un rango cuyo límite es el número de stickers
        while counter <= stickers.count():
            list.append(counter)
            counter += 1

        random.shuffle(list)  # desordena la list
        counter = 0

        # asigna los ordinales desordenados a cada ejemplar
        for cada_sticker in stickers:
            cada_sticker.ordinal = list[counter]
            cada_sticker.save()
            counter += 1

    def create_packs(self):  # crea los packs de la edición
        pack_list = []
        stickers = Decimal(Sticker.objects.filter(pack__isnull=True).count())
        limit = (stickers / self.collection.STICKERS_PER_PACK).quantize(
            Decimal('1'), rounding=ROUND_CEILING)

        counter = 1

        while counter <= limit:
            pack = Pack(ordinal=counter)
            pack_list.append(pack)

            if len(pack_list) >= 1000:
                Pack.objects.bulk_create(pack_list)
                pack_list = []

            counter += 1

        Pack.objects.bulk_create(pack_list)
        current_total = Pack.objects.all().count()

    def fill_packs(self):  # asigna los stickers a los  packs
        sticker_list = []
        packs = iter(Pack.objects.filter(box__isnull=True))

        stickers = iter(Sticker.objects.filter(
            pack__isnull=True).order_by('ordinal'))
        counter_stickers = 1

        while True:
            pack = next(packs, 'end_of_packs')

            if pack != 'end_of_packs':

                while True:
                    sticker = next(stickers, 'end_of_stickers')

                    if sticker != 'end_of_stickers':
                        sticker.pack = pack
                        sticker_list.append(sticker)
                        counter_stickers += 1

                        if counter_stickers > self.collection.STICKERS_PER_PACK:

                            counter_stickers = 1
                            break
                    else:
                        break

            else:
                break

        Sticker.objects.bulk_update(sticker_list, ['pack'])

    def shuffle_packs(self):  # desordena el atributo ordinal de los packs
        packs = Pack.objects.filter(box__isnull=True)
        list = []
        counter = 1

        while counter <= packs.count():  # llena una list auxiliar con los ordinales de los packs
            list.append(counter)
            counter += 1

        random.shuffle(list)  # desordena la list auxiliar
        counter = 0

        for each_pack in packs:  # reasigna los valores desordenados al atributo ordinal de cada pack
            each_pack.ordinal = list[counter]
            each_pack.save()
            counter += 1

    def create_boxes(self):  # crea los boxes correspondientes a la edition
        box_list = []
        total_packs = Pack.objects.filter(box__isnull=True).count()
        limit = Decimal(
            total_packs / self.collection.PACKS_PER_BOX).quantize(Decimal('1'), rounding=ROUND_CEILING)
        counter = 1

        while counter <= limit:
            box = Box(
                edition=self,
                ordinal=counter,
            )
            box_list.append(box)
            counter += 1

        Box.objects.bulk_create(box_list)

    def fill_boxes(self):  # asigna los packs a los boxes
        pack_list = []
        boxes = list(self.boxes.all())
        print("available boxes: ", len(boxes))
        standard_packs = list(
            Pack.objects.filter(
                box__isnull=True
            ).annotate(
                Count('stickers')
            ).exclude(
                stickers__coordinate__page=99
            ).order_by('ordinal')
        )
        print("standars packs: ", len(standard_packs))
        prize_packs = list(
            Pack.objects.filter(
                box__isnull=True
            ).annotate(
                Count('stickers')
            ).filter(
                stickers__coordinate__page=99
            ).order_by('ordinal')
        )
        print("prize packs: ", len(prize_packs))
        random_number_1 = random.randrange(
            1, self.collection.PACKS_PER_BOX)
        pack_counter = 1

        random_number_2 = 0

        while True:
            # determina la posicion en el box del segundo pack premiado
            random_number_2 = random.randrange(
                1, self.collection.PACKS_PER_BOX)
            """Como en el ciclo de llenado de los boxes al agregar un prize pack sea agrega
            un standar pack inmediatamente, se deben evitar aletorios contiuos hacia arriba o
            hacia abajo"""
            if (random_number_2 != random_number_1 and
                random_number_2 != (random_number_1 + 1) and
                    random_number_2 != (random_number_1 - 1)):
                break

        standard_packs_iter = iter(standard_packs)
        prize_packs_iter = iter(prize_packs)
        prize_counter = 0  # solo para us en prints
        for box in boxes:
            print("box: ", box)
            print("random 1: ", random_number_1)
            print("random 2: ", random_number_2)
            while True:
                # iteración pack cada pack
                standar_pack = next(standard_packs_iter, 'end_of_file')

                if standar_pack != 'end_of_file':

                    if pack_counter == random_number_1 or pack_counter == random_number_2:
                        print(
                            f"colocando{standar_pack} en posición {pack_counter}")
                        prize_pack = next(
                            prize_packs_iter, 'end_of_file')

                        if prize_pack != 'end_of_file':  # si la posicion es para pack premiado
                            # se guarda un pack premiado y uno standard
                            prize_pack.box = box
                            prize_pack.save()
                            # pack_list.append(prize_pack)
                            pack_counter += 1
                            standar_pack.box = box
                            pack_list.append(standar_pack)
                            pack_counter += 1
                            prize_counter += 1

                        else:  # si ya no hay packs premiados se guarda uno standard
                            print(
                                "No hay mas packs premiados, colocando standard pack en posicion: ", pack_counter)
                            standar_pack.box = box
                            pack_list.append(standar_pack)
                            pack_counter += 1
                            print("pack counter: ", pack_counter)
                    else:  # se guarda un pack standard
                        standar_pack.box = box
                        pack_list.append(standar_pack)
                        pack_counter += 1

                    if pack_counter > self.collection.PACKS_PER_BOX:  # si se alcanza el number de packs
                        # necesarios, se reinicia el counter
                        # de packs y se adelanta el counter de boxes
                        print("reiniciando contador para proximo box")
                        pack_counter = 1  # reinicio el counter de packs
                        # counter_boxes += 1 #adelanto el counter de boxes
                        # se recalculan las posiciones premiadas
                        random_number_1 = random.randrange(
                            1, self.collection.PACKS_PER_BOX)

                        while True:
                            random_number_2 = random.randrange(
                                1, self.collection.PACKS_PER_BOX)

                            if (random_number_2 != random_number_1
                                    and random_number_2 != (random_number_1 + 1)):

                                break  # salgo del bucle de los aleatorios
                        break  # y salgo del bucle de los packs

                else:
                    print("prize packs boxed normal flow: ", len(list(
                        Pack.objects.filter(
                            box__isnull=False
                        ).annotate(
                            Count('stickers')
                        ).filter(
                            stickers__coordinate__page=99
                        ).order_by('ordinal'))
                    ))
                    # si se acabaron los packs standard y aun quedan premiados, se continúan
                    # colocando en el box
                    remaining_packs = list(
                        Pack.objects.filter(
                            box__isnull=True
                        ).annotate(
                            Count('stickers')
                        ).filter(
                            stickers__coordinate__page=99
                        ).order_by('ordinal')
                    )
                    print("remaining packs: ", len(remaining_packs))
                    remaining_packs_iter = iter(remaining_packs)

                    while True:
                        prize_pack = next(
                            remaining_packs_iter, 'end_of_file')

                        if prize_pack != 'end_of_file':
                            print(
                                f"colocando {prize_pack} en posición {pack_counter}")

                            prize_pack.box = box
                            prize_pack.save()
                            pack_counter += 1
                        else:
                            break
                    # sino salgo del bucle de los packs
                    break

            else:  # salgo del bucle de los boxes
                break

        Pack.objects.bulk_update(pack_list, ['box'])
        print("prize packs boxed: ", len(list(
            Pack.objects.filter(
                box__isnull=False
            ).annotate(
                Count('stickers')
            ).filter(
                stickers__coordinate__page=99
            ).order_by('ordinal'))
        ))
        print("prize packs unboxed: ", len(list(
            Pack.objects.filter(
                box__isnull=True
            ).annotate(
                Count('stickers')
            ).filter(
                stickers__coordinate__page=99
            ).order_by('ordinal'))
        ))

        print("standard packs boxed: ", len(list(
            Pack.objects.filter(
                box__isnull=False
            ).annotate(
                Count('stickers')
            ).exclude(
                stickers__coordinate__page=99
            ).order_by('ordinal'))))
        print("standard packs unboxed: ", len(list(
            Pack.objects.filter(
                box__isnull=True
            ).annotate(
                Count('stickers')
            ).exclude(
                stickers__coordinate__page=99
            ).order_by('ordinal'))))
        print("total packs unboxed: ",
              Pack.objects.filter(box__isnull=True).count())
        print("total packs boxed: ", Pack.objects.filter(
            box__isnull=False).count())

    # funcion que desordena el atributo ordinal de los boxes

    def shuffle_boxes(self):
        boxes = self.boxes.all()
        list = []
        counter = 1

        while counter <= boxes.count():
            list.append(counter)
            counter += 1

        random.shuffle(list)
        counter = 0

        for cada_box in boxes:
            cada_box.ordinal = list[counter]
            counter += 1

        Box.objects.bulk_update(boxes, ['ordinal'])


class Sticker(models.Model):  # instancia ejemplares de cada sticker definida en las coordinates
    pack = models.ForeignKey('Pack', null=True, blank=True,
                             on_delete=models.CASCADE, related_name='stickers')
    coordinate = models.ForeignKey(
        Coordinate, on_delete=models.CASCADE, null=True, related_name='stickers')
    ordinal = models.IntegerField('Number ordinal de sticker')
    collector = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='stickers', null=True, blank=True)
    on_the_board = models.BooleanField(default=False)
    album = models.ForeignKey(
        'Album', on_delete=models.CASCADE, related_name='stickers', null=True)

    def __str__(self):
        return str(self.coordinate.number)

    @property
    # @admin.display(ordering='sticker__edition')
    def edition(self):
        return self.pack.box.edition

    @property
    def collection(self):
        return self.pack.box.edition.collection

    @property
    @admin.display()
    def number(self):
        return self.coordinate.number

    @property
    @admin.display(ordering='sticker__page')
    def page(self):
        return self.coordinate.page

    @property
    @admin.display(ordering='sticker__rarity_factor')
    def rarity(self):
        return self.coordinate.rarity_factor

    @property
    def box(self):
        return self.pack.box

    def stick(self, album_pk):
        slot = Slot.objects.get(
            page__album_id=album_pk,
            page__number=self.coordinate.page,
            number=self.coordinate.slot
        )
        slot.sticker = self
        slot.save(update_fields=['sticker'])


class Pack(models.Model):
    box = models.ForeignKey(
        'Box', null=True, blank=True, on_delete=models.CASCADE, related_name='packs')
    ordinal = models.BigIntegerField('pack_ordinal', default=0)
    sale = models.ForeignKey(
        'Sale', on_delete=models.CASCADE, null=True, related_name='packs')

    @property
    def edition(self):
        return self.box.edition

    def __str__(self):
        return 'Pack N°: ' + str(self.id)

    def open(self, user):
        """
        Aunque el collector de un pack puede ser inferido de la sale,
        es necesario redundar con este atributo porque en las operaciones de rescate
        las stickers cambian de dueño
        """

        for each_sticker in self.stickers.all():
            each_sticker.collector = user
            # each_sticker.en_tablero = True

            each_sticker.save()


class Box(models.Model):
    edition = models.ForeignKey(
        'Edition', on_delete=models.CASCADE, related_name='boxes')
    ordinal = models.BigIntegerField('ordinal_box', default=0)

    class Meta:
        verbose_name_plural = "boxes"
        ordering = ['ordinal',]

    def __str__(self):
        return f'Box N°: {self.id}, ordinal: {self.ordinal}'


class Album(models.Model):
    collector = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='albums')
    edition = models.ForeignKey(
        Edition, on_delete=models.CASCADE, related_name='albumes')

    def __str__(self):
        return str(self.edition.collection)

    class Meta:
        verbose_name_plural = 'Albums'

    @property
    def missing_stickers(self):
        slots = Slot.objects.filter(
            page__album=self, sticker__isnull=True).count()
        return slots

    @property
    def collected_stickers(self):
        slots = Slot.objects.filter(
            page__album=self, sticker__isnull=False).count()
        return slots

    @transaction.atomic
    def save(self, *args, **kwargs):
        super(Album, self).save(*args, **kwargs)
        self.create_pages()
        self.number_slots()

    def create_pages(self):
        pages = self.edition.collection.PAGES
        counter = 1

        while counter <= pages:
            Page.objects.create(album=self, number=counter)
            counter += 1

    def number_slots(self):
        slots = Slot.objects.filter(page__album=self).order_by('id')
        counter = 1

        for each_slot in slots:
            each_slot.absolut_number = counter
            each_slot.save()
            counter += 1


class Page(models.Model):
    album = models.ForeignKey(
        Album,
        on_delete=models.CASCADE,
        related_name='pages'
    )

    number = models.PositiveSmallIntegerField()

    @property
    def is_full(self):
        slots = Slot.objects.filter(
            page=self, sticker__isnull=True).count()

        if slots == 0:
            return True
        else:
            return False

    @property
    def prize_was_claimed(self):
        try:
            award = PagePrize.objects.get(page=self)
        except PagePrize.DoesNotExist:
            award = None

        if award == None:
            return False
        else:
            return True

    class Meta:
        ordering = ['number']

    @transaction.atomic
    def save(self, *args, **kwargs):
        super(Page, self).save(*args, **kwargs)
        lote_slots = []
        slots = self.album.edition.collection.SLOTS_PER_PAGE
        contador = 1

        while contador <= slots:
            slot = Slot(
                page=self,
                number=contador
            )
            lote_slots.append(slot)
            contador += 1

        Slot.objects.bulk_create(lote_slots)


class Slot(models.Model):
    page = models.ForeignKey(
        Page, on_delete=models.CASCADE,
        related_name='slots'
    )
    number = models.PositiveSmallIntegerField()
    sticker = models.OneToOneField(
        Sticker, on_delete=models.SET_NULL,
        null=True
    )
    absolut_number = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['number']

    def is_empty(self):
        if self.sticker == None:
            return True
        else:
            return False


class Sale(models.Model):
    """
    Sale de packs al collector.
    Los atributos edition, collector y quantity no cumplen estrictamente con la normalización
    ya que no conciernen estrictamente a la sale sino a los packs,
    pero la experiencia demostró que facilita las consultas y otras operaciones pack el modelo.
    Esto se bede a la política de vender packs de solo una collection por sale
    """
    date = models.DateField(default=timezone.now)
    edition = models.ForeignKey(
        Edition, on_delete=models.CASCADE, related_name='sales', null=True)
    dealer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sales',
        null=True
    )

    collector = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='purchases',
        null=True
    )

    quantity = models.SmallIntegerField()

    def __str__(self):
        return f'{self.id} / {self.date} / {self.collector}'

    @property
    def collection(self):
        return self.edition.collection

    def clean(self):
        """
        se consultan los packs en el insalerio del dealer
        para saber si hay suficientes para la sale, en caso contrario se genera
        error de validación
        """

        available_packs = Pack.objects.filter(
            sale__isnull=True,
            box__edition=self.edition,
            box__purchase__dealer=self.dealer
        ).order_by('ordinal').count()

        if available_packs < self.quantity:

            raise ValidationError(
                f'Inventario insuficiente: quedan {available_packs} sobres disponibles en inventario'
            )

    @transaction.atomic
    def save(self, *args, **kwargs):
        """
        Para relacionar los sobres correspondientes a a la venta actual
        y actualizar las opciones de rescate
        """
        super(Sale, self).save(*args, **kwargs)
        available_packs = Pack.objects.filter(
            sale__isnull=True,
            box__edition=self.edition,
            box__purchase__dealer=self.dealer
        ).order_by('ordinal')[:self.quantity]

        pack_list = []

        for each_pack in available_packs:
            each_pack.sale = self
            pack_list.append(each_pack)

        Pack.objects.bulk_update(pack_list, ['sale'])
        self.collector.rescue_options += self.quantity
        self.collector.save(update_fields=['rescue_options'])


class PagePrize(models.Model):
    page = models.OneToOneField(Page, on_delete=models.CASCADE, null=True)
    prize = models.ForeignKey(
        'StandardPrize', on_delete=models.CASCADE, null=True)

    def __str__(self):
        return str(self.prize)

    class Meta:
        verbose_name_plural = 'page prizes'
