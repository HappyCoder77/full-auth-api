import os
import shutil
from django.test.utils import override_settings
import tempfile

import datetime

from unittest import skip
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from promotions.test.factories import PromotionFactory
from collection_manager.models import Coordinate, SurprisePrize
from collection_manager.test.factories import (
    AlbumTemplateFactory,
    CollectionFactory,
)
from authentication.test.factories import UserFactory
from users.test.factories import CollectorFactory, DealerFactory
from ..models import Box, Pack, Sticker, StickerPrize
from .factories import EditionFactory

TEMP_MEDIA_ROOT = tempfile.mkdtemp()


# @skip("saltar")
@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class EditionTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        PromotionFactory()
        collection = CollectionFactory(album_template__with_coordinate_images=True)

        for each_prize in collection.standard_prizes.all():
            each_prize.description = "Bingo"
            each_prize.save()

        for each_prize in collection.surprise_prizes.all():
            each_prize.description = "Bingo"
            each_prize.save()

        cls.edition = EditionFactory.build(collection=collection, circulation=250)

        cls.edition.clean()
        cls.edition.save()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_edition_data(self):
        boxes = Box.objects.filter(edition=self.edition).order_by("pk")
        packs = Pack.objects.filter(
            box__in=Box.objects.filter(edition_id=self.edition.id)
        )
        self.assertEqual(self.edition.collection.box_cost, 150)
        self.assertEqual(
            str(self.edition),
            f"{self.edition.collection} ({self.edition.circulation})",
        )
        self.assertEqual(boxes.count(), 37)
        self.assertEqual(packs.count(), 3695)
        self.assertEqual(Pack.objects.all().count(), 3695)

    def test_rarity_distribution(self):
        stickers = Sticker.objects.all()

        rarity_1_total = Sticker.objects.filter(
            coordinate__rarity_factor=self.edition.collection.album_template.layout.RARITY_1
        ).count()

        rarity_2_total = Sticker.objects.filter(
            coordinate__rarity_factor=self.edition.collection.album_template.layout.RARITY_2
        ).count()

        rarity_3_total = Sticker.objects.filter(
            coordinate__rarity_factor=self.edition.collection.album_template.layout.RARITY_3
        ).count()

        rarity_4_total = Sticker.objects.filter(
            coordinate__rarity_factor=self.edition.collection.album_template.layout.RARITY_4
        ).count()

        rarity_5_total = Sticker.objects.filter(
            coordinate__rarity_factor=self.edition.collection.album_template.layout.RARITY_5
        ).count()

        rarity_6_total = Sticker.objects.filter(
            coordinate__rarity_factor=self.edition.collection.album_template.layout.RARITY_6
        ).count()

        rarity_7_total = Sticker.objects.filter(
            coordinate__rarity_factor=self.edition.collection.album_template.layout.RARITY_7
        ).count()

        surprize_prize_total = Sticker.objects.filter(
            coordinate__rarity_factor=self.edition.collection.album_template.layout.PRIZE_STICKER_RARITY
        ).count()

        total_stickers = (
            rarity_1_total
            + rarity_2_total
            + rarity_3_total
            + rarity_4_total
            + rarity_5_total
            + rarity_6_total
            + rarity_7_total
            + surprize_prize_total
        )

        self.assertEqual(rarity_1_total, 6000)
        self.assertEqual(rarity_2_total, 4000)
        self.assertEqual(rarity_3_total, 1000)
        self.assertEqual(rarity_4_total, 5)
        self.assertEqual(rarity_5_total, 2)
        self.assertEqual(rarity_6_total, 1)
        self.assertEqual(rarity_7_total, 1)
        self.assertEqual(surprize_prize_total, 74)
        self.assertEqual(stickers.count(), total_stickers)

    def test_boxes_content(self):
        boxes = Box.objects.filter(edition=self.edition).order_by("pk")

        for each_box in boxes:
            self.assertEqual(
                str(each_box), f"Box N°: {each_box.id}, ordinal: {each_box.ordinal}"
            )


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class EditionValidationTestCase(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_no_validation_raised(self):
        PromotionFactory()
        collection = CollectionFactory(album_template__with_coordinate_images=True)

        for each_prize in collection.standard_prizes.all():
            each_prize.description = "Bingo"
            each_prize.save()

        for each_prize in collection.surprise_prizes.all():
            each_prize.description = "Bingo"
            each_prize.save()

        edition = EditionFactory.build(collection=collection)

        try:
            edition.clean()
        except ValidationError:  # pragma: no cover
            self.fail(
                "clean() raised ValidationError unexpectedly!",
            )

    def test_coordinates_without_images(self):
        """Test validation when coordinates don't have images"""
        PromotionFactory()

        collection = CollectionFactory(with_prizes_defined=True)

        with self.assertRaises(ValidationError) as context:
            EditionFactory(collection=collection)

        error_messages = context.exception.messages
        self.assertTrue(
            any(
                "coordenadas sin imágenes asignadas" in message
                for message in error_messages
            )
        )

    def test_multiple_validation_errors(self):
        """Test that multiple validation errors are reported together"""
        PromotionFactory()

        with self.assertRaises(ValidationError) as context:
            EditionFactory()

        error_messages = context.exception.messages

        self.assertGreaterEqual(len(error_messages), 3)

    def test_no_standard_prizes_defined(self):
        PromotionFactory()
        collection = CollectionFactory()
        edition = EditionFactory.build(collection=collection)

        with self.assertRaises(ValidationError) as context:
            edition.full_clean()
        error_messages = context.exception.messages

        self.assertTrue(
            any(
                "La colección a la que se hace referencia tiene 4 premios standard sin definir"
                in message
                for message in error_messages
            )
        )

    def test_no_surprise_prizes_defined(self):
        PromotionFactory()
        collection = CollectionFactory(
            album_template__with_image=True, album_template__with_coordinate_images=True
        )
        edition = EditionFactory.build(collection=collection)

        for each_prize in collection.standard_prizes.all():
            each_prize.description = "Bingo"
            each_prize.save()

        with self.assertRaises(ValidationError) as context:
            edition.full_clean()

        error_messages = context.exception.messages

        self.assertTrue(
            any(
                "La colección a la que se hace referencia tiene 4 premios sorpresa sin definir. Revise e intente de nuevo guardar el registro"
                in message
                for message in error_messages
            )
        )

    def test_no_active_promotion(self):
        """Test validation when there's no active promotion"""
        # Create a promotion but set dates to make it inactive
        promotion = PromotionFactory(
            past=True,
        )
        with patch(
            "promotions.models.Promotion.objects.get_current"
        ) as mock_get_current:
            mock_get_current.return_value = promotion
            collection = CollectionFactory()

        with self.assertRaises(ValidationError) as context:
            EditionFactory(collection=collection)

        error_messages = context.exception.messages

        self.assertTrue(
            any(
                "No hay ninguna promoción activa en este momento; debe haber una promoción activa para crear una edición"
                in message
                for message in error_messages
            )
        )

    def test_collection_not_in_current_promotion(self):
        """Test validation when collection doesn't belong to current promotion"""
        PromotionFactory()

        future_promotion = PromotionFactory(
            future=True,
        )
        with patch(
            "promotions.models.Promotion.objects.get_current"
        ) as mock_get_current:
            mock_get_current.return_value = future_promotion
            collection = CollectionFactory()

            # Try to create edition with collection from different promotion
            edition = EditionFactory.build(collection=collection)

        with self.assertRaises(ValidationError) as context:
            edition.clean()

        error_messages = context.exception.messages

        self.assertTrue(
            any(
                "La colección seleccionada no pertenece a la promoción actual; solo se pueden crear ediciones de colecciones pertenecientes a la promoción actual"
                in message
                for message in error_messages
            )
        )


class PromotionMaxDebtTestCase(TestCase):
    def test_promotion_max_debt(self):
        promotion = PromotionFactory()
        CollectionFactory()
        CollectionFactory(album_template__name="Angela")

        self.assertEqual(promotion.max_debt, 150)


@skip
class AnalisisEditionTestCase(TestCase):  # pragma: no cover
    @classmethod
    def setUpTestData(cls):
        PromotionFactory()
        cls.edition = EditionFactory.build(circulation=1)
        cls.edition.collection.save()
        for each_prize in cls.edition.collection.standard_prizes.all():
            each_prize.description = "Bingo"
            each_prize.save()

        for each_prize in cls.edition.collection.surprise_prizes.all():
            each_prize.description = "Bingo"
            each_prize.save()

        cls.edition.clean()
        cls.edition.save()

    def test_edition_output(self):
        print("circulation: ", self.edition.circulation)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class StickerTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        PromotionFactory()
        cls.collection = CollectionFactory(
            album_template__with_coordinate_images=True, with_prizes_defined=True
        )

        cls.edition = EditionFactory(collection=cls.collection)
        cls.stickers = Sticker.objects.filter(
            pack__box__edition__collection=cls.collection
        ).order_by("ordinal")
        cls.collectible_stickers = cls.stickers.exclude(coordinate__page=99)
        cls.box = Box.objects.filter(edition=cls.edition).first()
        cls.packs = Pack.objects.filter(box__edition=cls.edition)
        cls.coordinates = Coordinate.objects.filter(
            template=cls.edition.collection.album_template,
        )

        cls.common_coordinates = cls.coordinates.filter(rarity_factor__gte=1)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.sticker = Sticker.objects.filter(coordinate__absolute_number__gt=0).first()

    def get_stickers_by_coordinate(self, coordinate_id):
        return self.stickers.filter(coordinate_id=coordinate_id).count()

    def get_stickers_by_pack(self, pack_id):
        return self.stickers.filter(pack=pack_id).count()

    def test_sticker_creation(self):
        self.assertEqual(self.stickers.count(), 45)
        self.assertEqual(self.collectible_stickers.count(), 44)

    def test_stickers_data(self):

        for each_sticker in self.stickers:
            self.assertFalse(each_sticker.is_repeated)
            self.assertFalse(each_sticker.on_the_board)
            self.assertFalse(each_sticker.is_rescued)
            self.assertIsNone(each_sticker.collector)
            self.assertEqual(each_sticker.box, self.box)
            self.assertEqual(
                str(each_sticker),
                f"Barajita nº {each_sticker.number}, {self.box.edition.collection}",
            )
            self.assertEqual(each_sticker.edition, self.edition)
            self.assertEqual(each_sticker.collection, self.edition.collection)
            self.assertEqual(
                each_sticker.number, each_sticker.coordinate.absolute_number
            )
            self.assertEqual(each_sticker.rarity, each_sticker.coordinate.rarity_factor)
            self.assertEqual(each_sticker.page, each_sticker.coordinate.page)

        for each_coordinate in self.common_coordinates:
            self.assertEqual(
                self.get_stickers_by_coordinate(each_coordinate.id),
                each_coordinate.rarity_factor * self.edition.circulation,
            )

        for each_pack in self.packs:
            self.assertLessEqual(
                self.get_stickers_by_pack(each_pack.id),
                self.edition.collection.album_template.layout.STICKERS_PER_PACK,
            )

        counter = 1

        for each_sticker in self.stickers:
            self.assertEqual(each_sticker.ordinal, counter)
            counter += 1

            try:
                each_sticker.slot
                self.fail(
                    "Sticker should not have a slot associated."
                )  # pragma: no cover
            except Sticker.slot.RelatedObjectDoesNotExist:
                self.assertTrue(True)

    def test_sticker_repeated_status(self):
        # Create a test user
        collector = CollectorFactory(user=UserFactory())

        # Get two stickers with the same coordinate in the same edition
        sticker1 = self.stickers.filter(coordinate__rarity_factor__gte=2).first()

        pack = sticker1.pack
        pack.open(collector.user)
        sticker1.refresh_from_db()

        sticker2 = (
            self.stickers.filter(coordinate=sticker1.coordinate)
            .exclude(id=sticker1.id)
            .first()
        )

        pack2 = sticker2.pack
        pack2.open(collector.user)
        sticker2.refresh_from_db()

        self.assertTrue(sticker2.is_repeated)

    def test_sticker_from_diferent_promotions_are_not_repeated(self):
        promotion = PromotionFactory(future=True)
        collector = CollectorFactory(user=UserFactory())

        with patch(
            "promotions.models.Promotion.objects.get_current"
        ) as mock_get_current:
            mock_get_current.return_value = promotion
            collection = CollectionFactory(
                album_template=self.collection.album_template,
                with_prizes_defined=True,
            )

            edition = EditionFactory(collection=collection)

            previous_coordinate = self.collection.album_template.coordinates.filter(
                rarity_factor__gte=2
            ).first()

            self.assertIsNotNone(
                previous_coordinate,
                "No coordinate with rarity_factor >= 2 found",
            )

            # Get all stickers for previous coordinate
            past_promotion_stickers = list(
                Sticker.objects.filter(
                    pack__box__edition=self.edition,
                    coordinate=previous_coordinate,
                )
            )
            # Ensure we have at least 2 stickers
            self.assertGreaterEqual(
                len(past_promotion_stickers),
                2,
                f"Expected at least 2 stickers for coordinate {previous_coordinate}, but found {len(past_promotion_stickers)}",
            )

            sticker1 = past_promotion_stickers[0]
            sticker2 = past_promotion_stickers[1]

            sticker1.pack.open(collector.user)
            sticker2.pack.open(collector.user)
            sticker1.refresh_from_db()
            sticker2.refresh_from_db()

            self.assertTrue(sticker2.is_repeated)

            # Get a sticker from new edition with same coordinate
            current_coordinate = edition.collection.album_template.coordinates.get(
                page=previous_coordinate.page,
                slot_number=previous_coordinate.slot_number,
            )

            current_promotion_sticker = Sticker.objects.filter(
                pack__box__edition=edition, coordinate=current_coordinate
            ).first()

            # Ensure we found a sticker in the new edition
            self.assertIsNotNone(
                current_promotion_sticker,
                f"No sticker found in new edition for coordinate page={previous_coordinate.page}, slot={previous_coordinate.slot_number}",
            )
            current_promotion_sticker.pack.open(collector.user)
            current_promotion_sticker.refresh_from_db()

            # Should not be repeated since it's from a different promotion
            self.assertFalse(current_promotion_sticker.is_repeated)

            # Test uncollected sticker
            uncollected_sticker = self.stickers.filter(
                coordinate__rarity_factor=1
            ).first()
            self.assertFalse(uncollected_sticker.is_repeated)

    def test_create_prize(self):
        prize_sticker = self.stickers.filter(coordinate__absolute_number=0).first()
        regular_sticker = self.stickers.filter(
            coordinate__absolute_number__gt=0
        ).first()

        # Test prize creation for prize sticker
        prize = prize_sticker.discover_prize()
        self.assertIsNotNone(prize)
        self.assertEqual(prize.sticker, prize_sticker)

        # Test prize creation for regular sticker
        with self.assertRaises(ValidationError):
            regular_sticker.discover_prize()

        # Test double prize creation
        with self.assertRaises(ValidationError):
            prize_sticker.discover_prize()

        # Test when no prizes available
        self.edition.collection.surprise_prizes.all().delete()
        prize_sticker_new = self.stickers.filter(coordinate__absolute_number=0).last()
        with self.assertRaises(ValidationError):
            prize_sticker_new.discover_prize()

    def test_check_is_repeated_edge_cases(self):
        # Test with no collector
        sticker = self.stickers.filter(
            pack__is_open=False, coordinate__rarity_factor=1
        ).first()
        self.assertFalse(sticker.check_is_repeated())

        # Test single sticker (not repeated)
        collector = CollectorFactory(user=UserFactory())
        sticker.pack.open(collector.user)
        sticker.refresh_from_db()
        self.assertFalse(sticker.check_is_repeated())

    def test_property_methods(self):
        sticker = self.stickers.first()

        self.assertEqual(sticker.edition, sticker.pack.box.edition)
        self.assertEqual(sticker.collection, sticker.pack.box.edition.collection)
        self.assertEqual(sticker.number, sticker.coordinate.absolute_number)
        self.assertEqual(sticker.page, sticker.coordinate.page)
        self.assertEqual(sticker.rarity, sticker.coordinate.rarity_factor)
        self.assertEqual(sticker.box, sticker.pack.box)
        self.assertFalse(sticker.is_rescued)

    def test_rescue_method(self):
        collector = CollectorFactory(user=UserFactory())
        self.sticker.rescue(collector.user)

        self.assertEqual(self.sticker.collector, collector.user)
        self.assertFalse(self.sticker.is_repeated)
        self.assertTrue(self.sticker.is_rescued)
        self.assertTrue(self.sticker.on_the_board)

    def test_rescue_sticker_with_no_collector(self):
        user = UserFactory()
        with self.assertRaises(ValidationError):
            self.sticker.rescue(user)

    def test_rescue_sticker_that_collector_already_owns(self):
        collector = CollectorFactory(user=UserFactory())
        self.sticker.collector = collector.user
        with self.assertRaises(ValidationError):
            self.sticker.rescue(collector.user)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class StickerPrizeTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        PromotionFactory()
        cls.collection = CollectionFactory(album_template__with_coordinate_images=True)
        for each_prize in cls.collection.standard_prizes.all():
            each_prize.description = "Bingo"
            each_prize.save()

        for each_prize in cls.collection.surprise_prizes.all():
            each_prize.description = "Bingo"
            each_prize.save()

        cls.edition = EditionFactory(collection=cls.collection)
        cls.dealer = DealerFactory(user=UserFactory())
        cls.collector = CollectorFactory(user=UserFactory())
        cls.user = UserFactory()

        cls.prized_sticker = Sticker.objects.filter(
            coordinate__absolute_number=0
        ).first()
        cls.pack = cls.prized_sticker.pack
        cls.pack.open(cls.collector.user)
        cls.prized_sticker.refresh_from_db()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.prized_sticker.discover_prize()
        self.prized_sticker.refresh_from_db()
        self.sticker_prize = self.prized_sticker.prize

    def test_sticker_prize_default_data(self):
        self.assertFalse(self.sticker_prize.claimed)
        self.assertIsNone(self.sticker_prize.claimed_date)
        self.assertIsNone(self.sticker_prize.claimed_by)
        self.assertEqual(self.sticker_prize.status, 1)
        self.assertEqual(
            str(self.sticker_prize),
            f"Premio sorpresa para barajita con el id {self.prized_sticker.id}: {self.sticker_prize.prize.description}",
        )

    def test_sticker_prize_data_after_claimed(self):
        self.sticker_prize.claim(self.dealer.user)
        self.sticker_prize.refresh_from_db()

        self.assertTrue(self.sticker_prize.claimed)
        self.assertEqual(self.sticker_prize.claimed_date, datetime.date.today())
        self.assertEqual(self.sticker_prize.claimed_by, self.dealer.user)
        self.assertEqual(self.sticker_prize.status, 2)

    def test_sticker_prize_validation(self):
        sticker = Sticker.objects.filter(coordinate__absolute_number__gt=0).first()
        prize = SurprisePrize.objects.first()
        sticker_prize = StickerPrize(sticker=sticker, prize=prize)

        with self.assertRaises(ValidationError):
            sticker_prize.full_clean()

    def test_claim_already_claimed_sticker_prize(self):
        self.sticker_prize.claim(self.dealer.user)
        self.sticker_prize.refresh_from_db()

        with self.assertRaises(ValidationError):
            self.sticker_prize.claim(self.dealer.user)

    def test_claim_sticker_prize_not_collector(self):

        with self.assertRaises(ValidationError):
            self.sticker_prize.claim(self.user)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class BoxTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        PromotionFactory()
        collection = CollectionFactory(album_template__with_coordinate_images=True)

        for each_prize in collection.standard_prizes.all():
            each_prize.description = "Bingo"
            each_prize.save()

        for each_prize in collection.surprise_prizes.all():
            each_prize.description = "Bingo"
            each_prize.save()

        cls.edition = EditionFactory.build(collection=collection)

        cls.edition.clean()
        cls.edition.save()
        cls.box = cls.edition.boxes.get(edition=cls.edition)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_box_data(self):
        self.assertEqual(self.box.edition, self.edition)
        self.assertEqual(self.box.ordinal, 1)
        self.assertEqual(Box.objects.all().count(), 1)
        self.assertEqual(
            str(self.box), f"Box N°: {self.box.id}, ordinal: {self.box.ordinal}"
        )


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PackTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        PromotionFactory()
        collection = CollectionFactory(album_template__with_coordinate_images=True)

        for each_prize in collection.standard_prizes.all():
            each_prize.description = "Bingo"
            each_prize.save()

        for each_prize in collection.surprise_prizes.all():
            each_prize.description = "Bingo"
            each_prize.save()

        cls.edition = EditionFactory(collection=collection)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_box_data(self):
        for box in self.edition.boxes.all():

            pack_counter = 1
            for pack in box.packs.all().order_by("ordinal"):
                self.assertEqual(pack.box, box)
                self.assertEqual(pack.ordinal, pack_counter)
                self.assertEqual(pack.edition, self.edition)
                self.assertEqual(str(pack), f"Pack N°: {pack.id}")

                pack_counter += 1

    def test_box_open_method(self):
        user = UserFactory()
        pack = Pack.objects.all().first()
        pack.open(user)

        for sticker in pack.stickers.all():
            self.assertEqual(sticker.pack, pack)
            self.assertEqual(sticker.collector, user)

            if sticker.number == 0:
                self.assertFalse(sticker.on_the_board)
                self.assertFalse(sticker.is_repeated)
