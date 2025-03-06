from django.contrib.auth import get_user_model
from django.db import models, transaction
from editions.models import Sticker
from datetime import date
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from editions.models import Edition, Pack, Sticker
from collection_manager.models import Collection

from collection_manager.models import StandardPrize


User = get_user_model()


class Album(models.Model):
    collector = models.ForeignKey(User, on_delete=models.CASCADE, related_name="albums")
    collection = models.ForeignKey(
        Collection, on_delete=models.CASCADE, related_name="albums"
    )

    def __str__(self):
        return f"{self.collection}"

    class Meta:
        verbose_name_plural = "Albums"
        unique_together = ("collector", "collection")

    @property
    def image(self):
        return self.collection.image

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
        pages = self.collection.layout.PAGES
        counter = 1

        while counter <= pages:
            Page.objects.create(album=self, number=counter)
            counter += 1

    def number_slots(self):

        slots = Slot.objects.filter(page__album=self).order_by("id")
        counter = 1

        for each_slot in slots:
            coordinate = self.collection.coordinates.get(absolute_number=counter)
            each_slot.absolute_number = counter
            each_slot.image = coordinate.image
            each_slot.save()
            counter += 1

    def pack_inbox(self):
        try:
            if Pack.objects.filter(
                collector=self.collector, box__collection=self.collection, is_open=False
            ).exists():
                return Pack.objects.filter(
                    collector=self.collector,
                    box__collection=self.collection,
                    is_open=False,
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
                pack__box__collection=self.collection,
                coordinate__absolute_number__gte=1,
                on_the_board=True,
            ).exists():
                return Sticker.objects.filter(
                    collector=self.collector,
                    pack__box__collection=self.collection,
                    coordinate__absolute_number__gte=1,
                    on_the_board=True,
                )
            else:
                return None

        except Exception:
            return None

    def prized_stickers(self):
        """
        Returns a queryset of stickers prized and undiscovered.
        """

        query = Sticker.objects.filter(
            collector=self.collector,
            pack__box__collection=self.collection,
            coordinate__absolute_number=0,
            prize__isnull=True,
            on_the_board=False,
        )

        return query if query.exists() else Sticker.objects.none()


class Page(models.Model):
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name="pages")
    number = models.PositiveSmallIntegerField()

    def __str__(self):
        return f"Album {self.album}: página {self.number}"

    @property
    def prize(self):
        prize = StandardPrize.objects.get(
            collection=self.album.collection, page=self.number
        )

        return prize

    @property
    def is_full(self):
        return not self.slots.filter(sticker__isnull=True).exists()

    @property
    def prize_was_created(self):
        return PagePrize.objects.filter(page=self).exists()

    @property
    def prize_was_claimed(self):
        return PagePrize.objects.filter(page=self, claimed_by__isnull=False)

    class Meta:
        ordering = ["number"]

    def create_prize(self):
        if hasattr(self, "page_prize"):
            raise ValidationError("Esta página ya tiene un premio asignado")

        prize = StandardPrize.objects.get(
            collection=self.album.collection, page=self.number
        )

        return PagePrize.objects.create(page=self, prize=prize)

    def create_slots(self):
        slot_list = []
        slots = self.album.collection.layout.SLOTS_PER_PAGE
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

        if sticker.collector != self.page.album.collector:
            raise ValueError("No puedes pegar una barajita que no te pertenece")

    class Meta:
        ordering = ["number"]

    @property
    def is_empty(self):
        return self.sticker is None

    @property
    def status(self):
        return "filled" if self.sticker else "empty"


class PagePrize(models.Model):
    PAGEPRIZE_STATUS = [
        (1, "No reclamado"),
        (2, "Reclamado"),
        (3, "En tránsito"),
        (4, "Entregado"),
    ]
    page = models.OneToOneField(
        Page, on_delete=models.CASCADE, null=True, related_name="page_prize"
    )
    prize = models.ForeignKey(StandardPrize, on_delete=models.CASCADE, null=True)
    claimed = models.BooleanField(default=False)
    claimed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    claimed_date = models.DateField(null=True, blank=True)
    status = models.SmallIntegerField(choices=PAGEPRIZE_STATUS, default=1)

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

    def clean(self):
        if self.page and not self.page.is_full:
            raise ValidationError(
                {"page": _("Cannot create a prize for an incomplete page.")}
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.prize)

    class Meta:
        verbose_name_plural = "page prizes"
