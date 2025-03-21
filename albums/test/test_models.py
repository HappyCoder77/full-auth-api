import os
import shutil
from django.test.utils import override_settings
import tempfile

from datetime import date
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from authentication.test.factories import UserFactory
from promotions.test.factories import PromotionFactory
from editions.models import Sticker
from editions.test.factories import EditionFactory
from collection_manager.models import Coordinate, StandardPrize
from collection_manager.test.factories import CollectionFactory
from users.test.factories import CollectorFactory, DealerFactory

from ..models import Slot, Page, Pack
from .factories import AlbumFactory

TEMP_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class AlbumTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        PromotionFactory()
        collection = CollectionFactory(
            album_template__with_coordinate_images=True, with_prizes_defined=True
        )
        EditionFactory(collection=collection)
        cls.album = AlbumFactory(
            collector__email="collector@example.com", collection=collection
        )
        cls.pages = cls.album.collection.album_template.layout.PAGES
        cls.slots = cls.album.collection.album_template.layout.SLOTS_PER_PAGE
        cls.total_slots = cls.slots * cls.pages

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_album_data(self):

        self.assertEqual(self.album.collector.email, "collector@example.com")
        self.assertEqual(str(self.album), f"Álbum {self.album.collection}")
        self.assertEqual(self.album.pages.count(), self.pages)
        self.assertEqual(Slot.objects.count(), self.total_slots)
        self.assertEqual(self.album.missing_stickers, 24)
        self.assertEqual(self.album.collected_stickers, 0)
        self.assertIsNone(self.album.stickers_on_the_board(), 0)
        self.assertQuerySetEqual(self.album.prized_stickers(), [])

    def test_unique_constraint(self):

        with self.assertRaises(IntegrityError):
            AlbumFactory(
                collector=self.album.collector, collection=self.album.collection
            )

    def test_prized_stickers(self):
        prized_sticker = Sticker.objects.filter(
            pack__box__edition__collection=self.album.collection,
            coordinate__absolute_number=0,
            prize__isnull=True,
            on_the_board=False,
        ).first()

        pack = prized_sticker.pack
        pack.open(self.album.collector)
        prized_sticker.refresh_from_db()

        self.assertEqual(self.album.prized_stickers().count(), 1)
        self.assertFalse(prized_sticker.on_the_board)
        self.assertFalse(prized_sticker.is_repeated)
        self.assertEqual(prized_sticker.collector, self.album.collector)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PageTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        PromotionFactory()
        cls.album = AlbumFactory()
        cls.pages = cls.album.collection.album_template.layout.PAGES
        cls.slots = cls.album.collection.album_template.layout.SLOTS_PER_PAGE

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_pages_data(self):

        page_counter = 1
        for page in self.album.pages.all().order_by("number"):

            self.assertEqual(page.album, self.album)
            self.assertEqual(page.number, page_counter)
            self.assertEqual(page.prize.page, page_counter)
            self.assertEqual(str(page.prize), page.prize.description)
            self.assertFalse(page.is_full)
            self.assertFalse(page.prize_was_created)
            self.assertEqual(page.slots.count(), self.slots)
            page_counter += 1


class SlotTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        PromotionFactory()
        cls.album = AlbumFactory()
        cls.pages = cls.album.collection.album_template.layout.PAGES
        cls.slots = cls.album.collection.album_template.layout.SLOTS_PER_PAGE
        cls.total_slots = cls.slots * cls.pages

    def test_album_pages_slots_data(self):
        page_counter = 1
        slot_absolute_counter = 1
        for page in self.album.pages.all():
            slot_counter = 1
            for slot in page.slots.all().order_by("number"):
                coordinate = self.album.collection.album_template.coordinates.get(
                    absolute_number=slot_absolute_counter
                )
                self.assertEqual(slot.page, page)
                self.assertEqual(slot.number, slot_counter)
                self.assertEqual(slot.absolute_number, slot_absolute_counter)
                self.assertEqual(slot.image, coordinate.image)
                self.assertTrue(slot.is_empty)
                slot_counter += 1
                slot_absolute_counter += 1
            page_counter += 1


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class StickStickerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        PromotionFactory()
        collection = CollectionFactory(
            album_template__with_coordinate_images=True, with_prizes_defined=True
        )
        edition = EditionFactory(collection=collection)
        cls.album = AlbumFactory(collection=edition.collection)

        for page in cls.album.pages.all():

            for slot in page.slots.all():
                sticker = Sticker.objects.filter(
                    coordinate__absolute_number=slot.absolute_number
                ).first()

                if not sticker is None:
                    slot.sticker = sticker
                    slot.save()

        cls.empty_slot = Slot.objects.filter(sticker__isnull=True).first()
        coordinate = Coordinate.objects.create(
            template=cls.album.collection.album_template,
            page=cls.empty_slot.page.number,
            slot_number=cls.empty_slot.number,
            absolute_number=cls.empty_slot.absolute_number,
            rarity_factor=0.5,
        )

        sticker = Sticker.objects.create(
            coordinate=coordinate, collector=cls.album.collector, ordinal=99
        )

        cls.empty_slot.place_sticker(sticker)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_place_sticker_method(self):
        self.assertEqual(self.album.missing_stickers, 3)
        self.assertEqual(self.album.collected_stickers, 21)
        self.assertTrue(self.empty_slot.page.is_full)

    def test_place_sticker_already_filled(self):
        slot = Slot.objects.filter(sticker__isnull=False).first()
        coordinate = Coordinate.objects.create(
            template=self.album.collection.album_template,
            page=slot.page.number,
            slot_number=slot.number,
            absolute_number=slot.absolute_number,
            rarity_factor=1,
        )

        sticker = Sticker.objects.create(
            coordinate=coordinate, collector=slot.page.album.collector, ordinal=99
        )

        with self.assertRaises(ValueError) as context:
            slot.place_sticker(sticker)

        self.assertEqual(
            str(context.exception), f"La casilla número {slot.number} ya está llena"
        )

    def test_place_sticker_wrong_number(self):
        slot = Slot.objects.filter(sticker__isnull=True).first()
        coordinate = Coordinate.objects.create(
            template=self.album.collection.album_template,
            page=slot.page.number,
            slot_number=slot.number,
            absolute_number=slot.absolute_number + 1,
            rarity_factor=1,
        )

        sticker = Sticker.objects.create(
            coordinate=coordinate, collector=slot.page.album.collector, ordinal=99
        )

        with self.assertRaises(ValueError) as context:
            slot.place_sticker(sticker)

        self.assertEqual(
            str(context.exception),
            f"Casilla equivocada. Intentas pegar la barajita número {sticker.number} en la casilla número {slot.number}",
        )


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PagePrizeTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        PromotionFactory()
        collection = CollectionFactory(
            album_template__with_coordinate_images=True, with_prizes_defined=True
        )
        coordinate = Coordinate.objects.get(rarity_factor=0.02)
        coordinate.rarity_factor = 1
        coordinate.save()
        edition = EditionFactory(collection=collection)
        cls.user = UserFactory()
        cls.dealer = DealerFactory(user=UserFactory())
        cls.collector = CollectorFactory(user=UserFactory())
        cls.album = AlbumFactory(
            collector=cls.collector.user, collection=edition.collection
        )
        cls.page = Page.objects.get(number=1)
        cls.packs = Pack.objects.all()

        for pack in cls.packs:
            pack.open(cls.album.collector)

        stickers = Sticker.objects.filter(coordinate__absolute_number__lte=6)

        for slot in cls.page.slots.all():
            sticker = stickers.filter(
                coordinate__absolute_number=slot.absolute_number
            ).first()

            slot.place_sticker(sticker)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.prize = StandardPrize.objects.get(page=self.page.number)
        self.page_prize = self.page.create_prize()

    def test_page_prize_data(self):

        self.assertEqual(self.page_prize.page, self.page)
        self.assertEqual(self.page_prize.prize.description, self.prize.description)
        self.assertFalse(self.page_prize.claimed)
        self.assertIsNone(self.page_prize.claimed_date)
        self.assertIsNone(self.page_prize.claimed_by)
        self.assertEqual(self.page_prize.status, 1)
        self.assertEqual(str(self.page_prize), self.prize.description)

    def test_claim_method(self):
        self.page_prize.claim(self.dealer.user)

        self.assertTrue(self.page_prize.claimed)
        self.assertEqual(self.page_prize.claimed_date, date.today())
        self.assertEqual(self.page_prize.claimed_by, self.dealer.user)
        self.assertEqual(self.page_prize.status, 2)

    def test_create_prize_for_an_incomplete_page(self):
        page = Page.objects.get(number=2)

        with self.assertRaises(ValidationError):
            page.create_prize()

    def claim_already_claimed_prize(self):
        self.page_prize.claim(self.dealer.user)

        with self.assertRaises(ValidationError):
            self.page_prize.claim(self.dealer.user)

    def test_not_dealer_claim_prize(self):
        with self.assertRaises(ValidationError):
            self.page_prize.claim(self.user)
