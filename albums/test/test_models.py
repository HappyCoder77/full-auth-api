from django.db import IntegrityError
from django.test import TestCase

from promotions.test.factories import PromotionFactory
from editions.models import Sticker
from collection_manager.models import Coordinate

from ..models import Slot
from .factories import AlbumFactory


class AlbumTestCase(TestCase):
    @ classmethod
    def setUpTestData(cls):
        promotion = PromotionFactory()
        cls.album = AlbumFactory(
            collector__email="albumcollector@example.com",
            edition__promotion=promotion,
            edition__collection__name="Los Simpsons"
        )
        cls.pages = cls.album.edition.collection.PAGES
        cls.slots = cls.album.edition.collection.SLOTS_PER_PAGE
        cls.total_slots = cls.slots * cls.pages

    def test_album_data(self):

        self.assertEqual(self.album.collector.email,
                         "albumcollector@example.com")
        self.assertEqual(self.album.edition.collection.name, "Los Simpsons")
        self.assertEqual(str(self.album), str(self.album.edition.collection))
        self.assertEqual(self.album.pages.count(), self.pages)
        self.assertEqual(
            Slot.objects.count(),
            self.total_slots
        )
        self.assertEqual(self.album.missing_stickers, 24)
        self.assertEqual(self.album.collected_stickers, 0)

    def test_unique_constraint(self):

        with self.assertRaises(IntegrityError):
            AlbumFactory(
                collector=self.album.collector,
                edition=self.album.edition
            )


class PageTestCase(TestCase):
    @ classmethod
    def setUpTestData(cls):
        promotion = PromotionFactory()
        cls.album = AlbumFactory(
            collector__email="albumcollector@example.com",
            edition__promotion=promotion,
            edition__collection__name="Los Simpsons"
        )
        cls.pages = cls.album.edition.collection.PAGES
        cls.slots = cls.album.edition.collection.SLOTS_PER_PAGE

    def test_pages_data(self):

        page_counter = 1
        for page in self.album.pages.all().order_by('number'):

            self.assertEqual(page.album, self.album)
            self.assertEqual(page.number, page_counter)
            self.assertEqual(page.standard_prize.page, page_counter)
            self.assertEqual(str(page.standard_prize),
                             page.standard_prize.description)
            self.assertFalse(page.is_full)
            self.assertFalse(page.prize_was_claimed)
            self.assertEqual(page.slots.count(), self.slots)
            page_counter += 1


class SlotTestCase(TestCase):
    @ classmethod
    def setUpTestData(cls):
        promotion = PromotionFactory()
        cls.album = AlbumFactory(
            collector__email="albumcollector@example.com",
            edition__promotion=promotion,
            edition__collection__name="Los Simpsons"
        )
        cls.pages = cls.album.edition.collection.PAGES
        cls.slots = cls.album.edition.collection.SLOTS_PER_PAGE
        cls.total_slots = cls.slots * cls.pages

    def test_album_pages_slots_data(self):
        page_counter = 1
        slot_absolute_counter = 1
        for page in self.album.pages.all():
            slot_counter = 1
            for slot in page.slots.all().order_by('number'):
                self.assertEqual(slot.page, page)
                self.assertEqual(slot.number, slot_counter)
                self.assertEqual(slot.absolute_number, slot_absolute_counter)
                self.assertTrue(slot.is_empty)
                slot_counter += 1
                slot_absolute_counter += 1
            page_counter += 1


class StickStickerTestCase(TestCase):
    @ classmethod
    def setUpTestData(cls):
        promotion = PromotionFactory()
        cls.album = AlbumFactory(
            collector__email="albumcollector@example.com",
            edition__promotion=promotion,
            edition__collection__name="Los Simpsons"
        )

        for page in cls.album.pages.all():

            for slot in page.slots.all():
                sticker = Sticker.objects.filter(
                    coordinate__absolute_number=slot.absolute_number).first()
                if not sticker is None:
                    slot.sticker = sticker
                    slot.save()

        cls.empty_slot = Slot.objects.filter(sticker__isnull=True).first()
        coordinate = Coordinate.objects.create(
            collection=cls.album.edition.collection,
            page=cls.empty_slot.page.number,
            slot_number=cls.empty_slot.number,
            absolute_number=cls.empty_slot.absolute_number,
            rarity_factor=0.5,
        )

        sticker = Sticker.objects.create(
            coordinate=coordinate,
            collector=cls.album.collector,
            ordinal=99
        )

        cls.empty_slot.stick_sticker(sticker)

    def test_stick_sticker_method(self):
        self.assertEqual(self.album.missing_stickers, 3)
        self.assertEqual(self.album.collected_stickers, 21)
        self.assertTrue(self.empty_slot.page.is_full)

    def test_stick_sticker_already_filled(self):
        slot = Slot.objects.filter(sticker__isnull=False).first()
        coordinate = Coordinate.objects.create(
            collection=self.album.edition.collection,
            page=slot.page.number,
            slot_number=slot.number,
            absolute_number=slot.absolute_number,
            rarity_factor=1,
        )

        sticker = Sticker.objects.create(
            coordinate=coordinate,
            collector=slot.page.album.collector,
            ordinal=99
        )

        with self.assertRaises(ValueError) as context:
            slot.stick_sticker(sticker)

        self.assertEqual(
            str(context.exception),
            f"La casilla número {slot.number} ya está llena"
        )

    def test_stick_sticker_wrong_number(self):
        slot = Slot.objects.filter(sticker__isnull=True).first()
        coordinate = Coordinate.objects.create(
            collection=self.album.edition.collection,
            page=slot.page.number,
            slot_number=slot.number,
            absolute_number=slot.absolute_number + 1,
            rarity_factor=1,
        )

        sticker = Sticker.objects.create(
            coordinate=coordinate,
            collector=slot.page.album.collector,
            ordinal=99
        )

        with self.assertRaises(ValueError) as context:
            slot.stick_sticker(sticker)

        self.assertEqual(
            str(context.exception),
            f"Casilla equivocada. intentas pegar la barajita número {sticker.number} en la casilla número {slot.number}"
        )
