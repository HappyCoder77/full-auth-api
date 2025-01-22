import datetime

from unittest import skip

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from promotions.test.factories import PromotionFactory
from collection_manager.models import Coordinate
from collection_manager.test.factories import CollectionFactory
from authentication.test.factories import UserFactory
from users.test.factories import CollectorFactory
from ..models import Box, Pack, Sticker
from .factories import EditionFactory


# @skip("saltar")
class EditionTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        PromotionFactory()
        cls.edition = EditionFactory.build(circulation=250)
        cls.edition.collection.save()
        for each_prize in cls.edition.collection.standard_prizes.all():
            each_prize.description = "Bingo"
            each_prize.save()

        for each_prize in cls.edition.collection.surprise_prizes.all():
            each_prize.description = "Bingo"
            each_prize.save()

        cls.edition.clean()
        cls.edition.save()

    def test_edition_data(self):
        boxes = Box.objects.filter(edition=self.edition).order_by("pk")
        packs = Pack.objects.filter(box__edition_id=self.edition.id)
        self.assertEqual(self.edition.box_cost, 150)
        self.assertEqual(str(self.edition), "Minecraft")
        self.assertEqual(boxes.count(), 37)
        self.assertEqual(packs.count(), 3695)

    def test_rarity_distribution(self):
        stickers = Sticker.objects.all()

        rarity_1_total = Sticker.objects.filter(
            coordinate__rarity_factor=self.edition.collection.RARITY_1
        ).count()

        rarity_2_total = Sticker.objects.filter(
            coordinate__rarity_factor=self.edition.collection.RARITY_2
        ).count()

        rarity_3_total = Sticker.objects.filter(
            coordinate__rarity_factor=self.edition.collection.RARITY_3
        ).count()

        rarity_4_total = Sticker.objects.filter(
            coordinate__rarity_factor=self.edition.collection.RARITY_4
        ).count()

        rarity_5_total = Sticker.objects.filter(
            coordinate__rarity_factor=self.edition.collection.RARITY_5
        ).count()

        rarity_6_total = Sticker.objects.filter(
            coordinate__rarity_factor=self.edition.collection.RARITY_6
        ).count()

        rarity_7_total = Sticker.objects.filter(
            coordinate__rarity_factor=self.edition.collection.RARITY_7
        ).count()

        surprize_prize_total = Sticker.objects.filter(
            coordinate__rarity_factor=self.edition.collection.PRIZE_STICKER_RARITY
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
        self.assertEqual(surprize_prize_total, 76)
        self.assertEqual(stickers.count(), total_stickers)

    def test_boxes_content(self):
        boxes = Box.objects.filter(edition=self.edition).order_by("pk")

        for each_box in boxes:
            self.assertEqual(
                str(each_box), f"Box N°: {each_box.id}, ordinal: {each_box.ordinal}"
            )


class EditionValidationTestCase(TestCase):

    def test_no_validation_raised(self):
        PromotionFactory()
        collection = CollectionFactory()
        edition = EditionFactory.build(collection=collection)

        for each_prize in edition.collection.standard_prizes.all():
            each_prize.description = "Bingo"
            each_prize.save()

        for each_prize in edition.collection.surprise_prizes.all():
            each_prize.description = "Bingo"
            each_prize.save()

        try:
            edition.clean()
        except ValidationError:  # pragma: no cover
            self.fail(
                "clean() raised ValidationError unexpectedly!",
            )

    def test_no_promotion_at_all(self):
        collection = CollectionFactory(name="Loolapaloza")
        edition = EditionFactory.build(collection=collection)

        with self.assertRaises(ValidationError) as context:
            edition.clean()
        error_messages = context.exception.messages
        self.assertTrue(
            any(
                "No hay ninguna promoción en curso." in message
                for message in error_messages
            )
        )

    def test_no_current_promotion(self):
        PromotionFactory(
            start_date=timezone.now() - datetime.timedelta(days=30), duration=29
        )
        collection = CollectionFactory(name="Angela")
        edition = EditionFactory.build(collection=collection)

        with self.assertRaises(ValidationError) as context:
            edition.full_clean()
        error_messages = context.exception.messages
        self.assertTrue(
            any(
                "No hay ninguna promoción en curso." in message
                for message in error_messages
            )
        )

    def test_collection_belongs_to_other_edition(self):
        PromotionFactory()
        edition = EditionFactory.build()
        edition.collection.save()

        for each_prize in edition.collection.standard_prizes.all():
            each_prize.description = "Bingo"
            each_prize.save()

        for each_prize in edition.collection.surprise_prizes.all():
            each_prize.description = "Bingo"
            each_prize.save()
        edition.clean()
        edition.save()

        edition2 = EditionFactory.build(collection=edition.collection)

        with self.assertRaises(ValidationError) as context:
            edition2.clean()
        error_messages = context.exception.messages
        self.assertTrue(
            any(
                "Ya existe una edición con la misma colección" in message
                for message in error_messages
            )
        )

    def test_no_standard_prizes_defined(self):
        promotion = PromotionFactory()
        collection = CollectionFactory()
        edition = EditionFactory.build(collection=collection)

        with self.assertRaises(ValidationError) as context:
            edition.full_clean()
        error_messages = context.exception.messages
        self.assertTrue(
            any(
                "La edición a la que se hace referencia parece no tener definidos los premios"
                in message
                for message in error_messages
            )
        )

    def test_no_surprise_prizes_defined(self):
        promotion = PromotionFactory()
        collection = CollectionFactory()
        edition = EditionFactory.build(collection=collection)

        for each_prize in collection.standard_prizes.all():
            each_prize.description = "Bingo"
            each_prize.save()

        with self.assertRaises(ValidationError) as context:
            edition.full_clean()

        error_messages = context.exception.messages
        self.assertTrue(
            any(
                "sorpresa. Revise e intente de nuevo guardar el registro" in message
                for message in error_messages
            )
        )


class PromotionMaxDebtTestCase(TestCase):
    def test_promotion_max_debt(self):
        promotion = PromotionFactory()
        EditionFactory(promotion=promotion, collection__name="Test Promotion")
        EditionFactory(promotion=promotion, collection__name="Test Promotion 2")

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


class StickerTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.edition = EditionFactory(promotion=PromotionFactory())

        for each_prize in cls.edition.collection.standard_prizes.all():
            each_prize.description = "Bingo"
            each_prize.save()

        for each_prize in cls.edition.collection.surprise_prizes.all():
            each_prize.description = "Bingo"
            each_prize.save()

        cls.stickers = Sticker.objects.all().order_by("ordinal")
        cls.collectible_stickers = cls.stickers.exclude(coordinate__page=99)
        cls.box = cls.edition.boxes.get(edition=cls.edition)
        cls.packs = Pack.objects.filter(box__edition=cls.edition)
        # como la edition es pequeña (1 ejemplar) para fines de test, omitimos rarezas inferiores a cero
        cls.coordinates = Coordinate.objects.filter(
            collection=cls.edition.collection,
        )
        cls.common_coordinates = cls.coordinates.filter(rarity_factor__gte=1)

    def get_stickers_by_coordinate(self, coordinate_id):
        return self.stickers.filter(coordinate_id=coordinate_id).count()

    def get_stickers_by_pack(self, pack_id):
        return self.stickers.filter(pack=pack_id).count()

    def test_sticker_creation(self):
        self.assertEqual(self.stickers.count(), 45)
        self.assertEqual(self.collectible_stickers.count(), 44)

    def test_stickers_data(self):

        for each_sticker in self.stickers:
            self.assertEqual(each_sticker.box, self.box)
            self.assertEqual(str(each_sticker), str(each_sticker.number))
            self.assertEqual(each_sticker.edition, self.edition)
            self.assertEqual(each_sticker.collection, self.edition.collection)
            self.assertEqual(each_sticker.edition, self.edition)
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
                self.edition.collection.STICKERS_PER_PACK,
            )
        counter = 1
        for each_sticker in self.stickers:
            self.assertEqual(each_sticker.ordinal, counter)
            counter += 1
            self.assertEqual(str(each_sticker), str(each_sticker.number))
            self.assertEqual(each_sticker.edition, self.edition)
            self.assertEqual(each_sticker.collection, self.edition.collection)
            self.assertEqual(
                each_sticker.number, each_sticker.coordinate.absolute_number
            )
            self.assertEqual(each_sticker.page, each_sticker.coordinate.page)
            self.assertEqual(each_sticker.rarity, each_sticker.coordinate.rarity_factor)
            self.assertEqual(each_sticker.box, each_sticker.pack.box)
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
        collector = CollectorFactory(user=UserFactory())
        promotion = PromotionFactory(future=True)
        edition = EditionFactory(
            promotion=promotion, collection=self.edition.collection
        )

        coordinate = self.edition.collection.coordinates.filter(rarity_factor=2).first()
        previous_edition_stickers = self.stickers.filter(
            coordinate=coordinate
        ).order_by("id")

        sticker1 = previous_edition_stickers[0]
        sticker2 = previous_edition_stickers[1]
        pack1 = sticker1.pack
        pack1.open(collector.user)
        sticker1.refresh_from_db()

        pack2 = sticker2.pack
        pack2.open(collector.user)
        sticker2.refresh_from_db()

        self.assertTrue(sticker2.is_repeated)

        # Get a sticker from new edition with same coordinate
        current_sticker = Sticker.objects.filter(
            pack__box__edition=edition, coordinate=coordinate
        ).first()

        pack3 = current_sticker.pack
        pack3.open(collector.user)
        current_sticker.refresh_from_db()

        # Should not be repeated since it's from a different edition
        self.assertFalse(current_sticker.is_repeated)

        # Test uncollected sticker
        uncollected_sticker = self.stickers.filter(coordinate__rarity_factor=1).first()
        self.assertFalse(uncollected_sticker.is_repeated)


class BoxTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        PromotionFactory()
        cls.edition = EditionFactory.build()
        cls.edition.collection.save()
        for each_prize in cls.edition.collection.standard_prizes.all():
            each_prize.description = "Bingo"
            each_prize.save()

        for each_prize in cls.edition.collection.surprise_prizes.all():
            each_prize.description = "Bingo"
            each_prize.save()

        cls.edition.clean()
        cls.edition.save()
        cls.box = cls.edition.boxes.get(edition=cls.edition)

    def test_box_data(self):
        self.assertEqual(self.box.edition, self.edition)
        self.assertEqual(self.box.ordinal, 1)
        self.assertEqual(Box.objects.all().count(), 1)
        self.assertEqual(
            str(self.box), f"Box N°: {self.box.id}, ordinal: {self.box.ordinal}"
        )


class PackTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        promotion = PromotionFactory()
        cls.edition = EditionFactory(promotion=promotion)

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
