import random
import logging

from collections import deque
from decimal import Decimal, ROUND_CEILING, ROUND_DOWN

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Case, When
from django.utils import timezone
from datetime import date

from promotions.models import Promotion
from collection_manager.models import Collection, Coordinate, SurprisePrize

logger = logging.getLogger(__name__)
User = get_user_model()


class Edition(models.Model):
    """
    Represents a specific printing run of a collection within a promotion.
    Handles sticker generation, pack creation, and box distribution.
    """

    BATCH_SIZE = 1000
    MIN_PACK_POSITION = 1
    MIN_PRIZES_POSITON_GAP = 10
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, db_index=True)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    circulation = models.DecimalField(
        max_digits=20, decimal_places=0, default=Decimal("1")
    )

    class Meta:
        verbose_name = "Edition"
        verbose_name_plural = "Editions"
        indexes = [
            models.Index(fields=["promotion", "collection"]),
            models.Index(fields=["circulation"]),
        ]

    def get_distribution_stats(self):
        """Returns key statistics about the edition distribution"""
        cache_key = f"edition_{self.id}_stats"
        stats = cache.get(cache_key)

        if stats is None:
            stats = {
                "total_boxes": self.boxes.count(),
                "total_packs": Pack.objects.filter(box__edition=self).count(),
                "prize_packs": Pack.objects.filter(
                    box__edition=self, stickers__coordinate__page=99
                )
                .distinct()
                .count(),
                "standard_packs": Pack.objects.filter(box__edition=self)
                .exclude(stickers__coordinate__page=99)
                .distinct()
                .count(),
            }
            cache.set(cache_key, stats, timeout=3600)

        return stats

    def validate_distribution(self):
        """Validates the complete distribution of the edition"""
        validations = {
            "prize_distribution": self.validate_prize_distribution(),
            "pack_counts": self.validate_pack_counts(),
            "box_integrity": self.validate_box_integrity(),
        }
        return all(validations.values()), validations

    def validate_prize_distribution(self):
        """Ensures correct prize pack distribution"""
        boxes = self.boxes.all().order_by("pk")
        total_boxes = boxes.count()

        if total_boxes == 0:
            return True

        # Check all boxes except the last one
        for box in boxes[: total_boxes - 1]:
            prize_packs = (
                box.packs.filter(stickers__coordinate__page=99).distinct().count()
            )
            if prize_packs != 2:
                return False

        return True

    def validate_pack_counts(self):
        """Validates pack counts in boxes"""
        boxes = self.boxes.all().order_by("pk")
        total_boxes = boxes.count()
        # Check all boxes except the last one
        for box in boxes[: total_boxes - 1]:
            if box.packs.count() != self.collection.PACKS_PER_BOX:
                return False

        # Last box can have fewer packs - no validation needed
        return True

    def validate_box_integrity(self):
        """Ensures boxes have correct pack arrangement"""
        return all(self._validate_single_box(box) for box in self.boxes.all())

    def _validate_single_box(self, box):
        """Helper method to validate individual box integrity"""
        packs = box.packs.all()

        # Only validate that:
        # 1. Pack ordinals are unique
        # 2. Each pack has at least one sticker
        return len(set(pack.ordinal for pack in packs)) == len(packs) and all(
            pack.stickers.count() > 0 for pack in packs
        )

    @property
    def box_cost(self):
        return self.promotion.pack_cost * self.collection.PACKS_PER_BOX

    def __str__(self):
        return f"{self.collection.name} {self.promotion}"

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
        self.create_stickers()
        self.shuffle_stickers()
        self.create_packs()
        self.fill_packs()
        self.shuffle_packs()
        self.create_boxes()
        self.fill_boxes()
        self.shuffle_boxes()

    def create_stickers(self):
        with transaction.atomic():
            BATCH_SIZE = 5000
            sticker_list = []
            ordinal = 1
            prize_rarity = self.collection.PRIZE_STICKER_RARITY
            coordinates = list(self.collection.coordinates.select_related())

            limits = {
                coord: (coord.rarity_factor * self.circulation).quantize(
                    Decimal("1"),
                    rounding=(
                        ROUND_CEILING
                        if coord.rarity_factor == prize_rarity
                        else ROUND_DOWN
                    ),
                )
                for coord in coordinates
            }

            for coordinate, limit in limits.items():
                for _ in range(int(limit)):
                    sticker = Sticker(
                        coordinate=coordinate,
                        ordinal=ordinal,
                    )
                    sticker_list.append(sticker)
                    ordinal += 1

                    if len(sticker_list) >= BATCH_SIZE:
                        Sticker.objects.bulk_create(sticker_list)
                        sticker_list.clear()

            if sticker_list:
                Sticker.objects.bulk_create(sticker_list)

    def shuffle_stickers(self):
        BATCH_SIZE = 5000

        with transaction.atomic():
            total_stickers = Sticker.objects.filter(pack__isnull=True).count()

            ordinal_numbers = list(range(1, total_stickers + 1))
            random.shuffle(ordinal_numbers)

            for start in range(0, total_stickers, BATCH_SIZE):
                end = start + BATCH_SIZE
                batch_stickers = list(
                    Sticker.objects.filter(pack__isnull=True)
                    .only("id", "ordinal")
                    .order_by("ordinal")[start:end]
                )

                updates = {
                    sticker.id: ordinal_numbers[i]
                    for i, sticker in enumerate(batch_stickers, start=start)
                }

                cases = [
                    When(id=sticker_id, then=ordinal)
                    for sticker_id, ordinal in updates.items()
                ]

                Sticker.objects.filter(id__in=updates.keys()).update(
                    ordinal=Case(*cases)
                )

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
        # logging.info(f"Total de packs creados: {current_total}")

    def remove_excess_prize_stickers(self):
        """
        Ensures exactly 2 prize stickers per box by removing excess ones
        """
        total_boxes = self.boxes.count()
        needed_prize_stickers = total_boxes * 2
        # logging.info(f"Needed prize stickers: {needed_prize_stickers}")
        prize_stickers = Sticker.objects.filter(
            pack__box__isnull=True, coordinate__absolute_number=0
        )
        # logging.info(f"Total prize stickers: {prize_stickers.count()}")
        excess_count = prize_stickers.count() - needed_prize_stickers
        # logging.info(f"Excess prize stickers: {excess_count}")

        if excess_count > 0:
            excess_sticker_ids = prize_stickers.values_list("id", flat=True)[
                :excess_count
            ]
            Sticker.objects.filter(id__in=excess_sticker_ids).delete()
        # logging.info(f"Total prize stickers after removal: {prize_stickers.count()}")

    def fill_packs(self):
        skipped_prized_stickers = deque()
        sticker_list = []
        packs = list(Pack.objects.filter(box__isnull=True))
        stickers = list(Sticker.objects.filter(pack__isnull=True).order_by("ordinal"))

        for pack in packs:
            prized_sticker_in_pack = False
            stickers_in_pack = 0

            while stickers_in_pack < self.collection.STICKERS_PER_PACK:

                if not stickers and not skipped_prized_stickers:
                    break

                sticker = (
                    stickers.pop(0) if stickers else skipped_prized_stickers.popleft()
                )

                if sticker.coordinate.absolute_number == 0:
                    if prized_sticker_in_pack:
                        skipped_prized_stickers.append(sticker)
                        continue
                    prized_sticker_in_pack = True

                sticker.pack = pack
                sticker_list.append(sticker)
                stickers_in_pack += 1

            if len(sticker_list) >= self.BATCH_SIZE:
                Sticker.objects.bulk_update(sticker_list, ["pack"])
                sticker_list.clear()

        if sticker_list:
            Sticker.objects.bulk_update(sticker_list, ["pack"])

    def shuffle_packs(self):  # desordena el atributo ordinal de los packs
        pack_list = list(Pack.objects.filter(box__isnull=True))
        ordinals = list(range(1, len(pack_list) + 1))
        random.shuffle(ordinals)

        counter = 1

        for i, pack in enumerate(pack_list):
            pack.ordinal = ordinals[i]

        Pack.objects.bulk_update(pack_list, ["ordinal"], batch_size=self.BATCH_SIZE)

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

    def _generate_prize_positions(self):
        """Generate random positions for prize packs with significant spacing."""
        positions = set()

        while len(positions) < 2:
            pos = random.randrange(1, self.collection.PACKS_PER_BOX)
            if not any(abs(pos - p) <= self.MIN_PRIZES_POSITON_GAP for p in positions):
                positions.add(pos)
        return sorted(positions)

    def _fill_single_box(
        self, box, prize_positions, standard_packs, prize_packs, pack_list
    ):
        """
        Fill a box with packs. The last box can contain fewer packs than expected.
        Returns the number of packs placed in the box.
        """
        pack_counter = 0
        position = 1
        # logging.info(f"Placing packs in box {box.id}")
        box_packs = []
        # logging.info(f"Prize positions for box {box.id}: {prize_positions}")
        packs_to_place = min(
            self.collection.PACKS_PER_BOX, len(standard_packs) + len(prize_packs)
        )
        # logging.info(f"Packs to place in box {box.id}: {packs_to_place}")
        # if packs_to_place < 100:

        # logging.info(f"Starting to fill box {box.id}")
        # logging.info(f"Prize positions: {prize_positions}")
        # logging.info(f"Available standard packs: {len(standard_packs)}")
        # logging.info(f"Available prize packs: {len(prize_packs)}")

        while position <= packs_to_place:
            pack_counter = position
            # if packs_to_place < 100:
            # logging.info(f"Pack counter: {pack_counter}")

            if pack_counter in prize_positions and prize_packs:
                pack = prize_packs.pop(0)
                # if packs_to_place < 100:
                # logging.info(f"Position {position}: Placed prize pack")
            elif standard_packs:
                pack = standard_packs.pop(0)
                # if packs_to_place < 100:
                # logging.info(f"Position {position}: Placed standard pack")
            elif prize_packs:
                pack = prize_packs.pop(0)
                # logging.info(f"Position {position}: Placed prize pack")
            else:
                # logging.info("No more packs to place")

                break
            pack.box = box
            box_packs.append(pack)
            position += 1

        # logging.info(f"Total packs placed in box {box.id}: {len(box_packs)}")
        pack_list.extend(box_packs)

        # logger.info(f"Box {box.id} filled with {len(box_packs)} packs")
        if len(pack_list) >= self.BATCH_SIZE:
            Pack.objects.bulk_update(pack_list, ["box"])
            pack_list.clear()

        return len(box_packs)

    def fill_boxes(self):
        """
        Distributes packs into boxes ensuring prize pack distribution.
        Returns the total number of boxes filled.
        """
        prize_packs = list(
            Pack.objects.filter(box__isnull=True)
            .prefetch_related("stickers")
            .filter(stickers__coordinate__page=99)
            .distinct()
            .order_by("ordinal")
        )
        # logging.info(f"Prize packs before removal: {len(prize_packs)}")

        self.remove_excess_prize_stickers()
        pack_list = []
        total_packs_distributed = 0

        total_packs = Pack.objects.filter(box__isnull=True).count()
        # logging.info(f"Total packs before classification: {total_packs}")
        standard_packs = list(
            Pack.objects.filter(box__isnull=True)
            .prefetch_related("stickers")
            .exclude(stickers__coordinate__page=99)
            .distinct()
            .order_by("ordinal")
        )
        # logging.info(f"standard_packs: {len(standard_packs)}")

        prize_packs = list(
            Pack.objects.filter(box__isnull=True)
            .prefetch_related("stickers")
            .filter(stickers__coordinate__page=99)
            .distinct()
            .order_by("ordinal")
        )
        # logging.info(f"prize_packs: {len(prize_packs)}")
        remaining_packs = len(standard_packs) + len(prize_packs)

        # logging.info(f"Total packs after classification: {remaining_packs}")

        for box in self.boxes.iterator():
            packs_for_this_box = min(self.collection.PACKS_PER_BOX, remaining_packs)
            # # logging.info(f"Box {box.id} will receive {packs_for_this_box} packs")
            prize_positions = self._generate_prize_positions()
            packs_placed = self._fill_single_box(
                box, prize_positions, standard_packs, prize_packs, pack_list
            )
            total_packs_distributed += packs_placed
            # # logging.info(f"Total packs placed in box {box.id}: {packs_placed}")
            remaining_packs -= packs_placed
            # logging.info(f"Remaining packs: {remaining_packs}")
        if pack_list:
            Pack.objects.bulk_update(pack_list, ["box"])

        return self.boxes.count()

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
    is_rescued = models.BooleanField(default=False)

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

    def rescue(self, user):
        if not user.is_collector:
            raise ValidationError("Solo los coleccionistas pueden rescatar barajitas")

        if self.collector == user:
            raise ValidationError("No puedes rescatar tus propias barajitas repetidas")

        self.is_repeated = False
        self.collector = user
        self.on_the_board = True
        self.is_rescued = True
        self.save()


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
            raise ValidationError("Sólo los detallistas pueden reclamar premios")

        self.claimed_by = user
        self.claimed = True
        self.claimed_date = date.today()
        self.status = 2
        self.save()
