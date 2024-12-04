import random
from decimal import Decimal

from django.db import models, transaction


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
    image = models.ImageField(upload_to='images/collections/')

    def __str__(self):
        return self.name

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
                    slot_number=current_slot,
                    ordinal=current_slot,
                    absolute_number=counter,
                    rarity_factor=0
                )

                coordinates_list.append(coordinate)
                current_slot += 1
                counter += 1

            current_page += 1

        coordinate = Coordinate(  # creacion de las coordinates de la sticker premiada
            collection=self,
            page=self.PRIZE_STICKER_COORDINATE,
            slot_number=self.PRIZE_STICKER_COORDINATE,
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

            if each_coordinate.slot_number == 1 or each_coordinate.slot_number == 2:
                each_coordinate.rarity_factor = self.RARITY_1
            elif each_coordinate.slot_number == 3 or each_coordinate.slot_number == 4:
                each_coordinate.rarity_factor = self.RARITY_2
            elif each_coordinate.slot_number == 5:
                each_coordinate.rarity_factor = self.RARITY_3
            # asigno los factores de rarity mas elevados a una unica sticker por página
            elif each_coordinate.slot_number == 6:

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
    page = models.BigIntegerField('Página')
    slot_number = models.BigIntegerField('Casilla')
    absolute_number = models.BigIntegerField('Número absoluto', default=0)
    ordinal = models.BigIntegerField('Ordinal', default=0)
    rarity_factor = models.DecimalField(
        'Factor de rareza', max_digits=6, decimal_places=3)
    image = models.ImageField(
        upload_to='images/coordinates/', null=True, blank=True)

    def __str__(self):
        return str(self.absolute_number)

    class Meta:
        verbose_name_plural = "Coordinates"


class SurprisePrize(models.Model):
    #TODO: agregar undefined como valor por defecto
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
