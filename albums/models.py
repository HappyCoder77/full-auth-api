from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db import models, transaction
from editions.models import Sticker

from editions.models import Edition
from sticker_collections.models import StandardPrize

User = get_user_model()


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
    # TODO: Arreglar este método
    # def fill(self, album_pk):
    #     slot = Slot.objects.get(
    #         page__album_id=album_pk,
    #         page__number=self.coordinate.page,
    #         number=self.coordinate.slot
    #     )
    #     slot.sticker = self
    #     slot.save(update_fields=['sticker'])


class PagePrize(models.Model):
    page = models.OneToOneField(Page, on_delete=models.CASCADE, null=True)
    prize = models.ForeignKey(
        StandardPrize, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return str(self.prize)

    class Meta:
        verbose_name_plural = 'page prizes'
