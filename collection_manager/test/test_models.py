from django.db import IntegrityError, transaction
from django.test import TestCase

from ..models import Collection, SurprisePrize, Theme
from .factories import CollectionFactory, ThemeFactory


class ThemeTestCase(TestCase):
    def setUp(self):
        self.theme = ThemeFactory(with_image=True)

    def tearDown(self):
        """Clean up data after each test method."""
        self.theme.image.delete(save=False)
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


class CollectionTestCase(TestCase):
    COLLECTION_NAME = "Minecraft"

    def setUp(self):
        self.collection = CollectionFactory(with_image=True)

    def tearDown(self):
        """Clean up data after each test method."""
        self.collection.image.delete(save=False)
        Collection.objects.all().delete()

    def test_collection_data(self):
        standard_coordinates = self.collection.coordinates.exclude(page=99).count()

        self.assertEqual(standard_coordinates, 24)
        self.assertEqual(self.collection.name, self.COLLECTION_NAME)
        self.assertEqual(
            self.collection.image.name, "images/collections/collection_image.png"
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
