import random
from decimal import Decimal, ROUND_CEILING, ROUND_DOWN

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Count
from django.utils import timezone
from datetime import date

from promotions.models import Promotion
from collection_manager.models import Collection, Coordinate, SurprisePrize

User = get_user_model()


# TODO: This app should be renamed to casino or something like that
class Edition(models.Model):
    # clase para crear las editiones que se haran en cada promoción
    """TODO: Explorar una mecanica de creacion mas eficiente y menos propensa a errores.
    Podria ser creando pack y boxes
    sobre la marcha,consolidando el atributo edition en un solo lugar,
    Se podria crear un clase diagramado o algo asi para contener la configuracion del album
    crear rama para este trabajo exclusivamente"""

    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE)
    # TODO: este campo deberia null True porque se establece a traves del metodo clean
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    circulation = models.DecimalField(
        max_digits=20, decimal_places=0, default=Decimal("1")
    )

    class Meta:
        verbose_name = "Edition"
        verbose_name_plural = "Editions"

    @property
    def box_cost(self):
        return self.promotion.pack_cost * self.collection.PACKS_PER_BOX

    def __str__(self):
        return self.collection.name

    def clean(self):
        try:  # verifica que exista una promotion
            last_promotion = Promotion.objects.latest("end_date")
        except Promotion.DoesNotExist:
            last_promotion = None
        # valida la creación del registro dependiendo de si existe o no una promoción
        # anterior o, en caso de existir, que la misma no haya terminado

        if last_promotion == None or last_promotion.end_date < timezone.now().date():
            raise ValidationError(
                """No hay ninguna promoción en curso.
            Por lo tanto, debe crearla primero y luego
            intentar de nuevo agregar este registro"""
            )
        else:
            try:  # verifica que no exista otra collection con el mismo name
                collection = self.__class__.objects.get(
                    collection=self.collection, promotion=last_promotion
                )
            except self.__class__.DoesNotExist:
                collection = None

            if collection != None:
                raise ValidationError(
                    """Ya existe una edición con la misma colección;
                    quiza deberia considerar realizar una reedición."""
                )
            else:
                standard_prize = self.collection.standard_prizes.first()
                if standard_prize.description == "descripción de premio standard":
                    raise ValidationError(
                        """La edición a la que se hace referencia parece no tener definidos los premios
                        standard. Revise e intente de nuevo guardar el registro"""
                    )

                surprise_prize = self.collection.surprise_prizes.first()

                if surprise_prize.description == "descripción de premio sorpresa":
                    raise ValidationError(
                        """La edición a la que se hace referencia parece no tener definidos los prizes
                        sorpresa. Revise e intente de nuevo guardar el registro"""
                    )

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
                limit = (each_coordinate.rarity_factor * self.circulation).quantize(
                    Decimal("1"), rounding=ROUND_CEILING
                )
            else:
                limit = (each_coordinate.rarity_factor * self.circulation).quantize(
                    Decimal("1"), rounding=ROUND_DOWN
                )

            sticker_list = []

            while circulation_counter <= limit:
                sticker = Sticker(coordinate=each_coordinate, ordinal=ordinal)

                sticker_list.append(sticker)

                if len(sticker_list) >= 500:
                    Sticker.objects.bulk_create(sticker_list)
                    sticker_list = []
                circulation_counter += 1
                ordinal += 1

            Sticker.objects.bulk_create(sticker_list)

    # aplica orden aleatorio a los valores del atributo ordinal de los stickers

    def shuffle_stickers(self):
        stickers = Sticker.objects.filter(pack__isnull=True).only("ordinal")
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
            Decimal("1"), rounding=ROUND_CEILING
        )

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

        stickers = iter(Sticker.objects.filter(pack__isnull=True).order_by("ordinal"))
        counter_stickers = 1

        while True:
            pack = next(packs, "end_of_packs")

            if pack != "end_of_packs":

                while True:
                    sticker = next(stickers, "end_of_stickers")

                    if sticker != "end_of_stickers":
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

        Sticker.objects.bulk_update(sticker_list, ["pack"])

    def shuffle_packs(self):  # desordena el atributo ordinal de los packs
        packs = Pack.objects.filter(box__isnull=True)
        list = []
        counter = 1

        while (
            counter <= packs.count()
        ):  # llena una list auxiliar con los ordinales de los packs
            list.append(counter)
            counter += 1

        random.shuffle(list)  # desordena la list auxiliar
        counter = 0

        for (
            each_pack
        ) in (
            packs
        ):  # reasigna los valores desordenados al atributo ordinal de cada pack
            each_pack.ordinal = list[counter]
            each_pack.save()
            counter += 1

    def create_boxes(self):  # crea los boxes correspondientes a la edition
        box_list = []
        total_packs = Pack.objects.filter(box__isnull=True).count()
        limit = Decimal(total_packs / self.collection.PACKS_PER_BOX).quantize(
            Decimal("1"), rounding=ROUND_CEILING
        )
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
        # print("---------------------------filling boxes")
        # print("available stickers: ", Sticker.objects.all().count())
        print
        pack_list = []
        boxes = list(self.boxes.all())
        # print("available boxes: ", len(boxes))
        standard_packs = list(
            Pack.objects.filter(box__isnull=True)
            .annotate(Count("stickers"))
            .exclude(stickers__coordinate__page=99)
            .order_by("ordinal")
        )
        # print("standars packs: ", len(standard_packs))
        prize_packs = list(
            Pack.objects.filter(box__isnull=True)
            .annotate(Count("stickers"))
            .filter(stickers__coordinate__page=99)
            .order_by("ordinal")
        )
        # print("prize packs: ", len(prize_packs))
        random_number_1 = random.randrange(1, self.collection.PACKS_PER_BOX)
        pack_counter = 1

        random_number_2 = 0

        while True:
            # determina la posicion en el box del segundo pack premiado
            random_number_2 = random.randrange(1, self.collection.PACKS_PER_BOX)
            """Como en el ciclo de llenado de los boxes al agregar un prize pack sea agrega
            un standar pack inmediatamente, se deben evitar aletorios contiuos hacia arriba o
            hacia abajo"""
            if (
                random_number_2 != random_number_1
                and random_number_2 != (random_number_1 + 1)
                and random_number_2 != (random_number_1 - 1)
            ):
                break

        standard_packs_iter = iter(standard_packs)
        prize_packs_iter = iter(prize_packs)
        prize_counter = 0  # solo para us en prints
        for box in boxes:
            # print("box: ", box)
            # print("random 1: ", random_number_1)
            # print("random 2: ", random_number_2)
            while True:
                # iteración pack cada pack
                standar_pack = next(standard_packs_iter, "end_of_file")

                if standar_pack != "end_of_file":

                    if (
                        pack_counter == random_number_1
                        or pack_counter == random_number_2
                    ):
                        # print(
                        # f"colocando {standar_pack} en posición {pack_counter}")
                        prize_pack = next(prize_packs_iter, "end_of_file")

                        if (
                            prize_pack != "end_of_file"
                        ):  # si la posicion es para pack premiado
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
                            # print(
                            #     "No hay mas packs premiados, colocando standard pack en posicion: ", pack_counter)
                            standar_pack.box = box
                            pack_list.append(standar_pack)
                            pack_counter += 1
                            # print("pack counter: ", pack_counter)
                    else:  # se guarda un pack standard
                        standar_pack.box = box
                        pack_list.append(standar_pack)
                        pack_counter += 1

                    if (
                        pack_counter > self.collection.PACKS_PER_BOX
                    ):  # si se alcanza el number de packs
                        # necesarios, se reinicia el counter
                        # de packs y se adelanta el counter de boxes
                        # print("reiniciando contador para proximo box")
                        pack_counter = 1  # reinicio el counter de packs
                        # counter_boxes += 1 #adelanto el counter de boxes
                        # se recalculan las posiciones premiadas
                        random_number_1 = random.randrange(
                            1, self.collection.PACKS_PER_BOX
                        )

                        while True:
                            random_number_2 = random.randrange(
                                1, self.collection.PACKS_PER_BOX
                            )

                            if (
                                random_number_2 != random_number_1
                                and random_number_2 != (random_number_1 + 1)
                            ):

                                break  # salgo del bucle de los aleatorios
                        break  # y salgo del bucle de los packs

                else:
                    # print("prize packs boxed normal flow: ", len(list(
                    #     Pack.objects.filter(
                    #         box__isnull=False
                    #     ).annotate(
                    #         Count('stickers')
                    #     ).filter(
                    #         stickers__coordinate__page=99
                    #     ).order_by('ordinal'))
                    # ))
                    # si se acabaron los packs standard y aun quedan premiados, se continúan
                    # colocando en el box
                    remaining_packs = list(
                        Pack.objects.filter(box__isnull=True)
                        .annotate(Count("stickers"))
                        .filter(stickers__coordinate__page=99)
                        .order_by("ordinal")
                    )
                    # print("remaining packs: ", len(remaining_packs))
                    remaining_packs_iter = iter(remaining_packs)

                    while True:
                        prize_pack = next(remaining_packs_iter, "end_of_file")

                        if prize_pack != "end_of_file":
                            # print(
                            #     f"colocando {prize_pack} en posición {pack_counter}")

                            prize_pack.box = box
                            prize_pack.save()
                            pack_counter += 1
                        else:
                            break
                    # sino salgo del bucle de los packs
                    break

            else:  # salgo del bucle de los boxes
                break

        Pack.objects.bulk_update(pack_list, ["box"])
        # print("prize packs boxed: ", len(list(
        #     Pack.objects.filter(
        #         box__isnull=False
        #     ).annotate(
        #         Count('stickers')
        #     ).filter(
        #         stickers__coordinate__page=99
        #     ).order_by('ordinal'))
        # ))
        # print("prize packs unboxed: ", len(list(
        #     Pack.objects.filter(
        #         box__isnull=True
        #     ).annotate(
        #         Count('stickers')
        #     ).filter(
        #         stickers__coordinate__page=99
        #     ).order_by('ordinal'))
        # ))

        # print("standard packs boxed: ", len(list(
        #     Pack.objects.filter(
        #         box__isnull=False
        #     ).annotate(
        #         Count('stickers')
        #     ).exclude(
        #         stickers__coordinate__page=99
        #     ).order_by('ordinal'))))
        # print("standard packs unboxed: ", len(list(
        #     Pack.objects.filter(
        #         box__isnull=True
        #     ).annotate(
        #         Count('stickers')
        #     ).exclude(
        #         stickers__coordinate__page=99
        #     ).order_by('ordinal'))))
        # print("total packs unboxed: ",
        #       Pack.objects.filter(box__isnull=True).count())
        # print("total packs boxed: ", Pack.objects.filter(
        #     box__isnull=False).count())

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

        Box.objects.bulk_update(boxes, ["ordinal"])


class Box(models.Model):
    edition = models.ForeignKey(Edition, on_delete=models.CASCADE, related_name="boxes")
    ordinal = models.BigIntegerField("ordinal_box", default=0)

    class Meta:
        verbose_name_plural = "boxes"
        ordering = [
            "ordinal",
        ]

    def __str__(self):
        return f"Box N°: {self.id}, ordinal: {self.ordinal}"


# Maybe collector field is unnecessary because SaleDetail already has it
class Pack(models.Model):
    collector = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="packs", null=True
    )
    box = models.ForeignKey(
        Box, null=True, blank=True, on_delete=models.CASCADE, related_name="packs"
    )
    ordinal = models.BigIntegerField("pack_ordinal", default=0)
    is_open = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["collector", "is_open"]),
        ]

    @property
    def edition(self):
        return self.box.edition

    def __str__(self):
        return f"Pack N°: {self.id}"

    @transaction.atomic
    def open(self, user):
        """
        Aunque el collector de un pack puede ser inferido de la sale,
        es necesario redundar con este atributo porque en las operaciones de rescate
        las stickers cambian de dueño
        """
        self.is_open = True
        self.save()

        for each_sticker in self.stickers.all():
            each_sticker.collector = user
            each_sticker.save()
            if each_sticker.number > 0:
                each_sticker.is_repeated = each_sticker.check_is_repeated()
                each_sticker.on_the_board = not each_sticker.is_repeated
                each_sticker.save()


class Sticker(models.Model):
    # instancia ejemplares de cada sticker definida en las coordinates
    pack = models.ForeignKey(
        Pack, null=True, blank=True, on_delete=models.CASCADE, related_name="stickers"
    )
    coordinate = models.ForeignKey(
        Coordinate, on_delete=models.CASCADE, null=True, related_name="stickers"
    )
    ordinal = models.IntegerField("Number ordinal de sticker")
    collector = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="stickers", null=True, blank=True
    )
    on_the_board = models.BooleanField(default=False)
    is_repeated = models.BooleanField(default=False)

    def check_is_repeated(self):
        """
        Returns True if the collector already has this sticker in their collection
        for the same edition
        """
        if not self.collector:
            return False

        query = Sticker.objects.filter(
            collector=self.collector,
            coordinate=self.coordinate,
            pack__box__edition=self.edition,
        ).exclude(id=self.id)

        return query.exists()

    def __str__(self):
        return str(self.coordinate.absolute_number)

    @property
    def edition(self):
        return self.pack.box.edition

    @property
    def collection(self):
        return self.pack.box.edition.collection

    @property
    @admin.display()
    def number(self):
        return self.coordinate.absolute_number

    @property
    @admin.display(ordering="sticker__page")
    def page(self):
        return self.coordinate.page

    @property
    @admin.display(ordering="sticker__rarity_factor")
    def rarity(self):
        return self.coordinate.rarity_factor

    @property
    def box(self):
        return self.pack.box

    def discover_prize(self):
        if self.coordinate.absolute_number != 0:
            raise ValidationError(
                "Solo las barajitas premiadas pueden descubrir premios sorpresa"
            )

        if hasattr(self, "prize"):
            raise ValidationError("Esta barajita ya tiene un premio asignado")

        random_prize = self.collection.get_random_surprise_prize()
        if not random_prize:
            raise ValidationError("No hay premios disponibles")

        return StickerPrize.objects.create(sticker=self, prize=random_prize)

    def has_prize_discovered(self):
        return hasattr(self, "prize")


class StickerPrize(models.Model):
    STICKERPRIZE_STATUS = [
        (1, "No reclamado"),
        (2, "Reclamado"),
        (3, "En tránsito"),
        (4, "Entregado"),
    ]
    sticker = models.OneToOneField(
        Sticker, on_delete=models.CASCADE, related_name="prize"
    )
    prize = models.ForeignKey(
        SurprisePrize,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sticker_prize",
    )
    claimed = models.BooleanField(default=False)
    claimed_date = models.DateField(null=True, blank=True)
    claimed_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL
    )
    status = models.SmallIntegerField(choices=STICKERPRIZE_STATUS, default=1)

    def clean(self):
        if self.sticker.coordinate.absolute_number != 0:
            raise ValidationError(
                "Solo las barajitas premiadas pueden obtener premio sorpresa"
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Premio sorpresa para barajita con el id {self.sticker.id}: {self.prize.description}"

    def claim(self, user):
        if self.claimed:
            raise ValidationError("Este premio ya ha sido reclamado")

        if not user.is_dealer:
            raise ValidationError("Sólo los coleccionistas pueden reclamar premios")

        self.claimed_by = user
        self.claimed = True
        self.claimed_date = date.today()
        self.status = 2
        self.save()
