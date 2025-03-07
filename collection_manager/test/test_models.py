from datetime import timedelta, date
import datetime
import os
from unittest import skip
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.test import TestCase
from django.utils import timezone
from django.core.files.storage import default_storage

from promotions.models import Promotion
from promotions.test.factories import PromotionFactory
from ..models import OldCollection, SurprisePrize, Theme, Collection, Layout
from .factories import OldCollectionFactory, ThemeFactory, CollectionFactory


class CollectionTestCase(TestCase):

    def setUp(self):
        PromotionFactory()
        self.collection = CollectionFactory(theme__with_image=True)
        self.promotion = Promotion.objects.first()
        self.layout = Layout.objects.first()

    def tearDown(self):
        """Clean up data after each test method."""
        self.collection.theme.image.delete(save=False)
        Collection.objects.all().delete()

    def test_str_method(self):
        self.assertEqual(
            str(self.collection), f"{self.collection.theme} {self.collection.promotion}"
        )

    def test_collection_theme_data(self):
        self.assertEqual(self.collection.theme.name, "Minecraft")
        self.assertTrue(self.collection.theme.image.name.startswith("images/themes/"))
        self.assertTrue(self.collection.theme.image.name.endswith(".png"))

    def test_collection_promotion_data(self):
        self.assertEqual(self.collection.promotion.start_date, date.today())
        self.assertEqual(self.collection.promotion.end_date, date.today())
        self.assertEqual(self.collection.promotion.duration, 1)
        self.assertEqual(self.collection.promotion.pack_cost, 1.5)
        self.assertFalse(self.collection.promotion.balances_created)
        self.assertEqual(str(self.collection.promotion), str(self.promotion))

    def test_collection_layout_data(self):
        self.assertEqual(self.collection.layout.PAGES, self.layout.PAGES)
        self.assertEqual(
            self.collection.layout.SLOTS_PER_PAGE, self.layout.SLOTS_PER_PAGE
        )
        self.assertEqual(
            self.collection.layout.STICKERS_PER_PACK, self.layout.STICKERS_PER_PACK
        )
        self.assertEqual(
            self.collection.layout.PACKS_PER_BOX, self.layout.PACKS_PER_BOX
        )
        self.assertEqual(
            self.collection.layout.PRIZE_STICKER_COORDINATE,
            self.layout.PRIZE_STICKER_COORDINATE,
        )
        self.assertEqual(
            self.collection.layout.SURPRISE_PRIZE_OPTIONS,
            self.layout.SURPRISE_PRIZE_OPTIONS,
        )
        self.assertEqual(self.collection.layout.RARITY_1, self.layout.RARITY_1)
        self.assertEqual(self.collection.layout.RARITY_2, self.layout.RARITY_2)
        self.assertEqual(self.collection.layout.RARITY_3, self.layout.RARITY_3)
        self.assertEqual(self.collection.layout.RARITY_4, self.layout.RARITY_4)
        self.assertEqual(self.collection.layout.RARITY_5, self.layout.RARITY_5)
        self.assertEqual(self.collection.layout.RARITY_6, self.layout.RARITY_6)
        self.assertEqual(self.collection.layout.RARITY_7, self.layout.RARITY_7)
        self.assertEqual(
            self.collection.layout.PRIZE_STICKER_RARITY,
            self.layout.PRIZE_STICKER_RARITY,
        )

    def test_rarity_distribution(self):
        expected_coordinates = self.layout.PAGES * self.layout.SLOTS_PER_PAGE
        self.assertEqual(
            self.collection.coordinates.exclude(page=99).count(), expected_coordinates
        )
        self.assertEqual(self.collection.coordinates.count(), expected_coordinates + 1)
        self.assertEqual(
            self.collection.coordinates.filter(
                rarity_factor=self.collection.layout.RARITY_2
            ).count(),
            8,
        )
        self.assertEqual(
            self.collection.coordinates.filter(
                rarity_factor=self.collection.layout.RARITY_3
            ).count(),
            4,
        )
        self.assertEqual(
            self.collection.coordinates.filter(
                rarity_factor=self.collection.layout.RARITY_4
            ).count(),
            1,
        )
        self.assertEqual(
            self.collection.coordinates.filter(
                rarity_factor=self.collection.layout.RARITY_5
            ).count(),
            1,
        )
        self.assertEqual(
            self.collection.coordinates.filter(
                rarity_factor=self.collection.layout.RARITY_6
            ).count(),
            1,
        )
        self.assertEqual(
            self.collection.coordinates.filter(
                rarity_factor=self.collection.layout.RARITY_7
            ).count(),
            1,
        )
        self.assertEqual(
            self.collection.coordinates.filter(
                rarity_factor=self.collection.layout.PRIZE_STICKER_RARITY
            ).count(),
            1,
        )
        self.assertEqual(
            self.collection.standard_prizes.count(), self.collection.layout.PAGES
        )
        self.assertEqual(
            self.collection.surprise_prizes.count(),
            self.collection.layout.SURPRISE_PRIZE_OPTIONS,
        )

    def test_coordinates_data(self):

        counter = 1
        current_page = 1

        while current_page <= self.collection.layout.PAGES:
            coordinates = iter(
                self.collection.coordinates.filter(page=current_page).order_by(
                    "slot_number"
                )
            )
            current_slot = 1

            while True:
                coordinate = next(coordinates, "fin_de_archivo")

                if coordinate != "fin_de_archivo":
                    self.assertEqual(coordinate.page, current_page)
                    self.assertEqual(coordinate.slot_number, current_slot)
                    self.assertEqual(coordinate.absolute_number, counter)
                    self.assertEqual(
                        str(coordinate),
                        f"Pagina:{coordinate.page}, Casilla nº: {coordinate.slot_number}, Nº absoluto: {coordinate.absolute_number}, rareza: {coordinate.rarity_factor}",
                    )
                    current_slot += 1
                    counter += 1
                else:
                    break

            current_page += 1

    def test_collection_unique_constraint(self):
        with transaction.atomic():
            with self.assertRaises(ValidationError):
                CollectionFactory(
                    theme=self.collection.theme, promotion=self.collection.promotion
                )

    def test_collection_relationships(self):
        self.assertIsNotNone(self.collection.promotion)
        self.assertIsNotNone(self.collection.theme)
        self.assertIsNotNone(self.collection.layout)

    def test_theme_protection(self):
        with self.assertRaises(ProtectedError):
            self.collection.theme.delete()

    def test_layout_protection(self):
        with self.assertRaises(ProtectedError):
            self.collection.layout.delete()

    def test_promotion_cascade(self):
        promotion_id = self.collection.promotion.id
        self.collection.promotion.delete()
        self.assertFalse(Collection.objects.filter(promotion_id=promotion_id).exists())

    def test_collection_filtering(self):
        theme2 = ThemeFactory(name="Angela")
        CollectionFactory(theme=theme2)
        self.assertEqual(
            Collection.objects.filter(theme=self.collection.theme).count(), 1
        )
        self.assertEqual(Collection.objects.count(), 2)

    def test_prize_coordinate_data(self):
        prize_coordinate = self.collection.coordinates.get(page=99)

        self.assertEqual(
            prize_coordinate.slot_number,
            self.collection.layout.PRIZE_STICKER_COORDINATE,
        )
        self.assertEqual(
            prize_coordinate.rarity_factor, self.collection.layout.PRIZE_STICKER_RARITY
        )
        self.assertEqual(prize_coordinate.ordinal, 0)

    def test_standard_prizes_data(self):
        for counter in range(1, self.collection.layout.PAGES + 1):
            standard_prize = self.collection.standard_prizes.get(page=counter)
            self.assertEqual(standard_prize.collection, self.collection)
            self.assertEqual(standard_prize.description, "undefined")
            self.assertEqual(standard_prize.__str__(), "undefined")

    def test_surprise_prizes_data(self):
        for counter in range(1, self.collection.layout.SURPRISE_PRIZE_OPTIONS + 1):
            surprise_prize = self.collection.surprise_prizes.get(number=counter)
            self.assertEqual(surprise_prize.description, "undefined")
            self.assertEqual(str(surprise_prize), "undefined")

    def test_clean_with_no_promotion(self):
        Promotion.objects.all().delete()

        collection = CollectionFactory.build(promotion=None)
        with self.assertRaises(ValidationError) as context:
            collection.full_clean()
        self.assertIn("No hay ninguna promoción en curso", str(context.exception))

    def test_no_current_promotion(self):
        Promotion.objects.all().delete()
        PromotionFactory(past=True)
        theme = ThemeFactory(name="barbie")
        collection = CollectionFactory.build(theme=theme)

        with self.assertRaises(ValidationError) as context:
            collection.full_clean()
        error_messages = context.exception.messages
        self.assertTrue(
            any(
                "No hay ninguna promoción en curso." in message
                for message in error_messages
            )
        )


class ThemeTestCase(TestCase):
    def setUp(self):
        self.theme = ThemeFactory(with_image=True)

    def tearDown(self):
        """Clean up data after each test method."""
        directory = os.path.dirname(self.theme.image.name)
        stored_files = default_storage.listdir(directory)[1]

        for filename in stored_files:
            if filename.startswith("test_image"):
                full_path = os.path.join(directory, filename)
                default_storage.delete(full_path)

    Theme.objects.all().delete()

    def test_theme_data(self):
        self.assertEqual(self.theme.name, "Minecraft")
        self.assertEqual(self.theme.image.name, "images/themes/test_image.png")
        self.assertEqual(str(self.theme), "Minecraft")

    def test_theme_unique_name_constraint(self):
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                ThemeFactory(with_image=True)

    def test_theme_verbose_names(self):
        self.assertEqual(Theme._meta.verbose_name, "theme")
        self.assertEqual(Theme._meta.verbose_name_plural, "themes")


@skip("deprecated model")
class OldCollectionTestCase(TestCase):
    COLLECTION_NAME = "Minecraft"

    def setUp(self):
        self.collection = OldCollectionFactory(with_image=True)

    def tearDown(self):
        """Clean up data after each test method."""
        self.collection.image.delete(save=False)
        OldCollection.objects.all().delete()

    def test_collection_data(self):
        standard_coordinates = self.collection.coordinates.exclude(page=99).count()

        self.assertEqual(standard_coordinates, 24)
        self.assertEqual(self.collection.name, self.COLLECTION_NAME)
        self.assertEqual(
            self.collection.image.name, "images/collections/test_image.png"
        )
        self.assertEqual(str(self.collection), "Minecraft")
        self.assertEqual(self.collection.coordinates.count(), 25)
        self.assertEqual(
            self.collection.coordinates.filter(
                rarity_factor=self.collection.RARITY_1
            ).count(),
            8,
        )
        self.assertEqual(
            self.collection.coordinates.filter(
                rarity_factor=self.collection.RARITY_2
            ).count(),
            8,
        )
        self.assertEqual(
            self.collection.coordinates.filter(
                rarity_factor=self.collection.RARITY_3
            ).count(),
            4,
        )
        self.assertEqual(
            self.collection.coordinates.filter(
                rarity_factor=self.collection.RARITY_4
            ).count(),
            1,
        )
        self.assertEqual(
            self.collection.coordinates.filter(
                rarity_factor=self.collection.RARITY_5
            ).count(),
            1,
        )
        self.assertEqual(
            self.collection.coordinates.filter(
                rarity_factor=self.collection.RARITY_6
            ).count(),
            1,
        )
        self.assertEqual(
            self.collection.coordinates.filter(
                rarity_factor=self.collection.RARITY_7
            ).count(),
            1,
        )
        self.assertEqual(
            self.collection.coordinates.filter(
                rarity_factor=self.collection.PRIZE_STICKER_RARITY
            ).count(),
            1,
        )
        self.assertEqual(self.collection.standard_prizes.count(), self.collection.PAGES)
        self.assertEqual(
            self.collection.surprise_prizes.count(),
            self.collection.SURPRISE_PRIZE_OPTIONS,
        )

    def test_prize_coordinate_data(self):
        prize_coordinate = self.collection.coordinates.get(page=99)

        self.assertEqual(
            prize_coordinate.slot_number, self.collection.PRIZE_STICKER_COORDINATE
        )
        self.assertEqual(
            prize_coordinate.rarity_factor, self.collection.PRIZE_STICKER_RARITY
        )
        self.assertEqual(prize_coordinate.ordinal, 0)

    def test_coordinates_data(self):

        counter = 1
        current_page = 1

        while current_page <= self.collection.PAGES:
            coordinates = iter(
                self.collection.coordinates.filter(page=current_page).order_by(
                    "slot_number"
                )
            )
            current_slot = 1

            while True:
                coordinate = next(coordinates, "fin_de_archivo")

                if coordinate != "fin_de_archivo":
                    self.assertEqual(coordinate.page, current_page)
                    self.assertEqual(coordinate.slot_number, current_slot)
                    self.assertEqual(coordinate.absolute_number, counter)
                    self.assertEqual(str(coordinate), str(counter))
                    current_slot += 1
                    counter += 1
                else:
                    break

            current_page += 1

    def test_standard_prizes_data(self):
        for counter in range(1, self.collection.PAGES + 1):
            standard_prize = self.collection.standard_prizes.get(page=counter)
            self.assertEqual(standard_prize.collection, self.collection)
            self.assertEqual(
                standard_prize.description, "descripción de premio standard"
            )
            self.assertEqual(standard_prize.__str__(), "descripción de premio standard")

    def test_surprise_prizes_data(self):
        for counter in range(1, self.collection.SURPRISE_PRIZE_OPTIONS + 1):
            surprise_prize = self.collection.surprise_prizes.get(number=counter)
            self.assertEqual(
                surprise_prize.description, "descripción de premio sorpresa"
            )
            self.assertEqual(str(surprise_prize), "descripción de premio sorpresa")


def test_get_random_surprise_prize(self):
    # Test that the method returns a valid SurprisePrize instance
    random_prize = self.collection.get_random_surprise_prize()
    self.assertIsInstance(random_prize, SurprisePrize)
    self.assertEqual(random_prize.collection, self.collection)

    # Test that the prize comes from the collection's surprise prizes
    self.assertIn(random_prize, self.collection.surprise_prizes.all())

    # Test multiple calls return different prizes (statistical test)
    prizes_set = {self.collection.get_random_surprise_prize() for _ in range(20)}
    # With 20 attempts, we should get at least 2 different prizes
    self.assertGreater(len(prizes_set), 1)


def test_get_random_surprise_prize_with_no_prizes(self):
    # Delete all surprise prizes
    self.collection.surprise_prizes.all().delete()

    # Test that the method handles empty prizes gracefully
    random_prize = self.collection.get_random_surprise_prize()
    self.assertIsNone(random_prize)
