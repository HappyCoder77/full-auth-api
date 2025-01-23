from django.contrib.auth import get_user_model
from django.db import models, transaction
from editions.models import Sticker

from editions.models import Edition, Pack, Sticker

from collection_manager.models import StandardPrize

User = get_user_model()


class Album(models.Model):
    collector = models.ForeignKey(User, on_delete=models.CASCADE, related_name="albums")
    edition = models.ForeignKey(
        Edition, on_delete=models.CASCADE, related_name="albumes"
    )

    def __str__(self):
        return str(self.edition.collection)

    class Meta:
        verbose_name_plural = "Albums"
        unique_together = ("collector", "edition")

    @property
    def missing_stickers(self):
        slots = Slot.objects.filter(page__album=self, sticker__isnull=True).count()
        return slots

    @property
    def collected_stickers(self):
        slots = Slot.objects.filter(page__album=self, sticker__isnull=False).count()
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

        slots = Slot.objects.filter(page__album=self).order_by("id")
        counter = 1

        for each_slot in slots:
            coordinate = self.edition.collection.coordinates.get(
                absolute_number=counter
            )
            each_slot.absolute_number = counter
            each_slot.image = coordinate.image
            each_slot.save()
            counter += 1

    def pack_inbox(self):
        try:
            if Pack.objects.filter(
                collector=self.collector, box__edition=self.edition, is_open=False
            ).exists():
                return Pack.objects.filter(
                    collector=self.collector, box__edition=self.edition, is_open=False
                )
            else:
                return None
        except Exception:
            return None

    def stickers_on_the_board(self):
        """
        Returns a queryset of stickers that are on the board for the collector of this album.
        """
        try:
            if Sticker.objects.filter(
                collector=self.collector,
                pack__box__edition=self.edition,
                coordinate__absolute_number__gte=1,
                on_the_board=True,
            ).exists():
                return Sticker.objects.filter(
                    collector=self.collector,
                    pack__box__edition=self.edition,
                    coordinate__absolute_number__gte=1,
                    on_the_board=True,
                )
            else:
                return None
        except Exception:
            return None


class Page(models.Model):
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name="pages")

    number = models.PositiveSmallIntegerField()

    @property
    def standard_prize(self):
        prize = StandardPrize.objects.get(
            collection=self.album.edition.collection, page=self.number
        )

        return prize

    @property
    def is_full(self):
        return Slot.objects.filter(page=self, sticker__isnull=True).count() <= 0

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
        ordering = ["number"]

    def create_slots(self):
        slot_list = []
        slots = self.album.edition.collection.SLOTS_PER_PAGE
        counter = 1

        while counter <= slots:
            slot = Slot(page=self, number=counter)
            slot_list.append(slot)
            counter += 1

        Slot.objects.bulk_create(slot_list)

    @transaction.atomic
    def save(self, *args, **kwargs):
        super(Page, self).save(*args, **kwargs)
        self.create_slots()


class Slot(models.Model):
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="slots")
    number = models.PositiveSmallIntegerField()
    sticker = models.OneToOneField(Sticker, on_delete=models.SET_NULL, null=True)
    absolute_number = models.PositiveSmallIntegerField(default=0)
    image = models.ImageField(null=True, blank=True)

    @transaction.atomic
    def place_sticker(self, sticker):
        self._validate_sticker_placement(sticker)
        self.sticker = sticker
        self.save()
        sticker.on_the_board = False
        sticker.save()
        return True

    def _validate_sticker_placement(self, sticker):
        if not self.is_empty:
            raise ValueError(f"La casilla número {self.number} ya está llena")

        if sticker.coordinate.absolute_number != self.absolute_number:
            raise ValueError(
                f"Casilla equivocada. Intentas pegar la barajita número {sticker.coordinate.absolute_number} en la casilla número {self.number}"
            )

    class Meta:
        ordering = ["number"]

    @property
    def is_empty(self):
        return self.sticker is None

    @property
    def status(self):
        return "filled" if self.sticker else "empty"


class PagePrize(models.Model):
    # TODO: candidato a eliminación; con un atributo booleano bastaría
    page = models.OneToOneField(Page, on_delete=models.CASCADE, null=True)
    prize = models.ForeignKey(StandardPrize, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return str(self.prize)

    class Meta:
        verbose_name_plural = "page prizes"
