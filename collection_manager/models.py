import os
import random
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import Manager
from django.db import models, transaction
from promotions.models import Promotion
from rest_framework.exceptions import NotFound
from promotions.models import Promotion
from django.db.models.signals import pre_delete
from django.dispatch import receiver


class Theme(models.Model):
    name = models.CharField("Nombre", max_length=50, unique=True)
    image = models.ImageField("Imagen", upload_to="images/themes/")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "theme"
        verbose_name_plural = "themes"


@receiver(pre_delete, sender=Theme)
def delete_theme_image(sender, instance, **kwargs):
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)


class Layout(models.Model):
    PAGES = 4
    SLOTS_PER_PAGE = 6
    STICKERS_PER_PACK = 3
    PACKS_PER_BOX = 100
    PRIZE_STICKER_COORDINATE = 99
    SURPRISE_PRIZE_OPTIONS = 4
    RARITY_1 = Decimal(3)
    RARITY_2 = Decimal(2)
    RARITY_3 = Decimal(1)
    RARITY_4 = Decimal(0.02).quantize(Decimal("0.00"))
    RARITY_5 = Decimal(0.01).quantize(Decimal("0.00"))
    RARITY_6 = Decimal(0.006).quantize(Decimal("0.000"))
    RARITY_7 = Decimal(0.004).quantize(Decimal("0.000"))
    PRIZE_STICKER_RARITY = Decimal(0.301).quantize(Decimal("0.000"))


class AlbumTemplate(Theme):
    layout = models.OneToOneField(
        Layout,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="album",
    )

    def __str__(self):
        return f"{self.name}"

    @transaction.atomic
    def save(self, *args, **kwargs):
        is_new = self._state.adding

        if is_new:
            self.layout = Layout.objects.create()
            super(AlbumTemplate, self).save(*args, **kwargs)
            self.create_coordinates()
            self.shuffle_coordinates()
            self.distribute_rarity()
        else:
            super(AlbumTemplate, self).save(*args, **kwargs)

    def create_coordinates(self):
        coordinates_list = []
        counter = 1
        current_page = 1

        while (
            current_page <= self.layout.PAGES
        ):  # bucle que recorre las pages del album
            current_slot = 1

            while (
                current_slot <= self.layout.SLOTS_PER_PAGE
            ):  # bucle que recorre las stickers de cada page,
                # y crea las coordinates correspondientes
                coordinate = Coordinate(
                    template=self,
                    page=current_page,
                    slot_number=current_slot,
                    ordinal=current_slot,
                    absolute_number=counter,
                    rarity_factor=0,
                )

                coordinates_list.append(coordinate)
                current_slot += 1
                counter += 1

            current_page += 1

        coordinate = Coordinate(  # creacion de las coordinates de la sticker premiada
            template=self,
            page=self.layout.PRIZE_STICKER_COORDINATE,
            slot_number=self.layout.PRIZE_STICKER_COORDINATE,
            rarity_factor=float(self.layout.PRIZE_STICKER_RARITY),
        )

        coordinates_list.append(coordinate)
        Coordinate.objects.bulk_create(coordinates_list)

    def shuffle_coordinates(self):
        coordinates_list = []
        current_page = 1

        while current_page <= self.layout.PAGES:
            page_coordinates = self.coordinates.filter(page=current_page)
            slots_count = page_coordinates.count()

            shuffle_list = list(range(1, slots_count + 1))
            random.shuffle(shuffle_list)

            for idx, coordinate in enumerate(page_coordinates):
                coordinate.ordinal = shuffle_list[idx]
                coordinates_list.append(coordinate)

            current_page += 1

        Coordinate.objects.bulk_update(coordinates_list, ["ordinal"])

    def distribute_rarity(self):

        coordinates_list = []
        # asigno los factores de rarity comun en función del número de sticker
        for each_coordinate in self.coordinates.all():

            if each_coordinate.ordinal == 1 or each_coordinate.ordinal == 2:
                each_coordinate.rarity_factor = self.layout.RARITY_1
            elif each_coordinate.ordinal == 3 or each_coordinate.ordinal == 4:
                each_coordinate.rarity_factor = self.layout.RARITY_2
            elif each_coordinate.ordinal == 5:
                each_coordinate.rarity_factor = self.layout.RARITY_3
            # asigno los factores de rarity mas elevados a una unica sticker por página
            elif each_coordinate.ordinal == 6:

                if each_coordinate.page == 1:
                    each_coordinate.rarity_factor = self.layout.RARITY_4
                if each_coordinate.page == 2:
                    each_coordinate.rarity_factor = self.layout.RARITY_5
                if each_coordinate.page == 3:
                    each_coordinate.rarity_factor = self.layout.RARITY_6
                if each_coordinate.page == 4:
                    each_coordinate.rarity_factor = self.layout.RARITY_7

            coordinates_list.append(each_coordinate)

        Coordinate.objects.bulk_update(coordinates_list, ["rarity_factor"])


class CollectionManager(Manager):
    def get_current_list(self):
        promotion = Promotion.objects.get_current()
        if not promotion:
            raise NotFound("No hay ninguna promocion en curso.")

        collections = Collection.objects.filter(promotion=promotion)

        if not collections.exists():
            raise NotFound(
                "No se ha creado ninguna collección para la promoción en curso."
            )

        return collections


class Collection(models.Model):
    """Represents a specific collection within a theme"""

    objects = CollectionManager()
    theme = models.ForeignKey(
        Theme, on_delete=models.PROTECT, related_name="collections"
    )
    promotion = models.ForeignKey(
        Promotion,
        on_delete=models.CASCADE,
        db_index=True,
        null=True,
        blank=True,
        related_name="collections",
    )
    layout = models.ForeignKey(
        Layout,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="collections",
    )

    @property
    def box_cost(self):
        return self.promotion.pack_cost * self.layout.PACKS_PER_BOX

    def __str__(self):
        return f"{self.theme} {self.promotion}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["theme", "promotion"], name="unique_collection"
            )
        ]

    def clean(self):
        current_promotion = Promotion.objects.get_current()

        if not current_promotion:
            raise ValidationError(
                """No hay ninguna promoción en curso.
            Por lo tanto, debe crearla primero y luego
            intentar de nuevo agregar este registro"""
            )

        self.promotion = current_promotion

    @transaction.atomic
    def save(self, *args, **kwargs):
        is_new = self._state.adding

        if is_new:
            self.layout = Layout.objects.create()
            self.full_clean()
            super(Collection, self).save(*args, **kwargs)

            self.create_coordinates()
            self.shuffle_coordinates()
            self.distribute_rarity()
            self.create_standard_prizes()
            self.create_surprise_prizes()
        else:
            super(Collection, self).save(*args, **kwargs)

    def create_coordinates(self):  # función que crea las coordinates de una colección
        coordinates_list = []
        counter = 1
        current_page = 1

        while (
            current_page <= self.layout.PAGES
        ):  # bucle que recorre las pages del album
            current_slot = 1

            while (
                current_slot <= self.layout.SLOTS_PER_PAGE
            ):  # bucle que recorre las stickers de cada page,
                # y crea las coordinates correspondientes
                coordinate = Coordinate(
                    collection=self,
                    page=current_page,
                    slot_number=current_slot,
                    ordinal=current_slot,
                    absolute_number=counter,
                    rarity_factor=0,
                )

                coordinates_list.append(coordinate)
                current_slot += 1
                counter += 1

            current_page += 1

        coordinate = Coordinate(  # creacion de las coordinates de la sticker premiada
            collection=self,
            page=self.layout.PRIZE_STICKER_COORDINATE,
            slot_number=self.layout.PRIZE_STICKER_COORDINATE,
            rarity_factor=float(self.layout.PRIZE_STICKER_RARITY),
        )

        coordinates_list.append(coordinate)
        Coordinate.objects.bulk_create(coordinates_list)

    def shuffle_coordinates(self):
        coordinates_list = []
        current_page = 1

        while current_page <= self.layout.PAGES:
            page_coordinates = self.coordinates.filter(page=current_page)
            slots_count = page_coordinates.count()

            shuffle_list = list(range(1, slots_count + 1))
            random.shuffle(shuffle_list)

            for idx, coordinate in enumerate(page_coordinates):
                coordinate.ordinal = shuffle_list[idx]
                coordinates_list.append(coordinate)

            current_page += 1

        Coordinate.objects.bulk_update(coordinates_list, ["ordinal"])

    def distribute_rarity(self):

        coordinates_list = []
        # asigno los factores de rarity comun en función del número de sticker
        for each_coordinate in self.coordinates.all():

            if each_coordinate.slot_number == 1 or each_coordinate.slot_number == 2:
                each_coordinate.rarity_factor = self.layout.RARITY_1
            elif each_coordinate.slot_number == 3 or each_coordinate.slot_number == 4:
                each_coordinate.rarity_factor = self.layout.RARITY_2
            elif each_coordinate.slot_number == 5:
                each_coordinate.rarity_factor = self.layout.RARITY_3
            # asigno los factores de rarity mas elevados a una unica sticker por página
            elif each_coordinate.slot_number == 6:

                if each_coordinate.page == 1:
                    each_coordinate.rarity_factor = self.layout.RARITY_4
                if each_coordinate.page == 2:
                    each_coordinate.rarity_factor = self.layout.RARITY_5
                if each_coordinate.page == 3:
                    each_coordinate.rarity_factor = self.layout.RARITY_6
                if each_coordinate.page == 4:
                    each_coordinate.rarity_factor = self.layout.RARITY_7

            coordinates_list.append(each_coordinate)

        Coordinate.objects.bulk_update(coordinates_list, ["rarity_factor"])

    def create_standard_prizes(self):
        pages = range(1, self.layout.PAGES + 1)

        for page in pages:
            StandardPrize.objects.create(
                collection_id=self.id,
                page=page,
            )

    def create_surprise_prizes(self):
        range_options = range(1, self.layout.SURPRISE_PRIZE_OPTIONS + 1)

        for counter in range_options:
            SurprisePrize.objects.create(
                collection_id=self.id,
                number=counter,
            )

    def get_random_surprise_prize(self):
        return random.choice(self.surprise_prizes.all())


class Coordinate(models.Model):
    template = models.ForeignKey(
        AlbumTemplate, on_delete=models.CASCADE, related_name="coordinates"
    )
    page = models.BigIntegerField("Página")
    slot_number = models.BigIntegerField("Casilla")
    absolute_number = models.BigIntegerField("Número absoluto", default=0)
    ordinal = models.BigIntegerField("Ordinal", default=0)
    rarity_factor = models.DecimalField(
        "Factor de rareza", max_digits=6, decimal_places=3
    )
    image = models.ImageField(upload_to="images/coordinates/", null=True, blank=True)

    def __str__(self):
        return f"Pagina:{self.page}, Casilla nº: {self.slot_number}, Nº absoluto: {self.absolute_number}, rareza: {self.rarity_factor}"

    class Meta:
        verbose_name_plural = "Coordinates"


@receiver(pre_delete, sender=Coordinate)
def delete_coordinate_image(sender, instance, **kwargs):
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)


class SurprisePrize(models.Model):
    collection = models.ForeignKey(
        Collection,
        on_delete=models.CASCADE,
        null=True,
        related_name="surprise_prizes",
    )
    number = models.SmallIntegerField(default=0)
    description = models.CharField(max_length=100, default="undefined")

    def __str__(self):
        return self.description

    class Meta:
        verbose_name = "surprise prize"
        verbose_name_plural = "surprise prizes"


class StandardPrize(models.Model):
    collection = models.ForeignKey(
        Collection,
        on_delete=models.CASCADE,
        null=True,
        related_name="standard_prizes",
    )
    page = models.SmallIntegerField()
    description = models.CharField(max_length=100, default="undefined")

    def __str__(self):
        return self.description

    class Meta:
        verbose_name_plural = "standard prizes"
