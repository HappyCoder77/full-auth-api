from datetime import timedelta, date
import datetime
import os
import shutil
from django.test.utils import override_settings
from django.conf import settings
import tempfile
from unittest import skip
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.test import TestCase
from django.utils import timezone
from django.core.files.storage import default_storage

from promotions.models import Promotion
from promotions.test.factories import PromotionFactory
from ..models import SurprisePrize, Theme, Collection, Layout
from .factories import ThemeFactory, CollectionFactory, AlbumTemplateFactory

TEMP_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class AlbumTemplateTestCase(TestCase):
    def setUp(self):
        self.album_template = AlbumTemplateFactory(
            with_image=True, with_coordinate_images=True
        )
        self.image_paths = []
        if self.album_template.image:
            self.image_paths.append(self.album_template.image.name)

        for coordinate in self.album_template.coordinates.all():
            if coordinate.image:
                self.image_paths.append(coordinate.image.name)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_album_template_data(self):
        expected_coordinates_count = (
            self.album_template.layout.PAGES * self.album_template.layout.SLOTS_PER_PAGE
            + 1
        )
        rare_coordinates = self.album_template.coordinates.filter(rarity_factor__lt=1.0)

        self.assertEqual(self.album_template.name, "Minecraft")
        self.assertEqual(self.album_template.image.name, "images/themes/test_image.png")
        self.assertEqual(str(self.album_template), "Minecraft")
        self.assertIsNotNone(self.album_template.layout)
        self.assertEqual(
            self.album_template.coordinates.all().count(), expected_coordinates_count
        )
        self.assertEqual(rare_coordinates.count(), 5)

    def test_unique_name_constraint(self):
        with self.assertRaises(IntegrityError):
            AlbumTemplateFactory()

    def test_rarity_distribution(self):

        for page in range(1, self.album_template.layout.PAGES + 1):
            page_coordinates = self.album_template.coordinates.filter(page=page)
            rare_in_page = page_coordinates.filter(ordinal=6)

            self.assertEqual(rare_in_page.count(), 1)
            rare_coordinate = rare_in_page.first()

            if page == 1:
                self.assertEqual(
                    rare_coordinate.rarity_factor, self.album_template.layout.RARITY_4
                )
            elif page == 2:
                self.assertEqual(
                    rare_coordinate.rarity_factor, self.album_template.layout.RARITY_5
                )
            elif page == 3:
                self.assertEqual(
                    rare_coordinate.rarity_factor, self.album_template.layout.RARITY_6
                )
            elif page == 4:
                self.assertEqual(
                    rare_coordinate.rarity_factor, self.album_template.layout.RARITY_7
                )

    def test_image_deletion_on_template_delete(self):
        image_path = self.album_template.image.path
        self.assertTrue(os.path.exists(image_path))
        self.album_template.delete()

        self.assertFalse(os.path.exists(image_path))

    def test_shuffle_coordinates(self):
        template = AlbumTemplateFactory(with_image=True, name="Angela")
        original_ordinals = list(template.coordinates.values_list("ordinal", flat=True))
        template.shuffle_coordinates()
        new_ordinals = list(template.coordinates.values_list("ordinal", flat=True))

        # Note: There's a small chance this could fail randomly if the shuffle
        # happens to produce the same order
        self.assertNotEqual(original_ordinals, new_ordinals)

    def test_coordinate_images_creation(self):
        """Test that images are properly created for coordinates."""

        album = AlbumTemplateFactory(
            name="Mario", with_image=True, with_coordinate_images=True
        )

        for coordinate in album.coordinates.all():
            self.assertIsNotNone(coordinate.image)
            self.assertTrue(coordinate.image.name.startswith("images/coordinates/"))
            self.assertTrue(default_storage.exists(coordinate.image.name))
            expected_prefix = f"coordinate_{coordinate.page}_{coordinate.slot_number}"
            self.assertTrue(
                os.path.basename(coordinate.image.name).startswith(expected_prefix)
            )

            with default_storage.open(coordinate.image.name) as f:
                image_content = f.read()
                self.assertGreater(len(image_content), 0)

            self.image_paths.append(coordinate.image.name)

    def test_coordinate_image_deletion(self):
        """Test that coordinate images are deleted when coordinates are deleted."""
        album = AlbumTemplateFactory(
            name="barbie", with_image=True, with_coordinate_images=True
        )

        # Get a coordinate and its image path
        coordinate = album.coordinates.first()
        image_path = coordinate.image.name

        # Verify the image exists
        self.assertTrue(default_storage.exists(image_path))

        # Delete the coordinate
        coordinate.delete()

        # Verify the image was deleted
        self.assertFalse(default_storage.exists(image_path))


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class CollectionTestCase(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        PromotionFactory()
        self.collection = CollectionFactory(
            album_template__with_image=True, album_template__with_coordinate_images=True
        )
        self.promotion = Promotion.objects.first()
        self.layout = Layout.objects.first()

    def test_str_method(self):
        self.assertEqual(
            str(self.collection),
            f"{self.collection.album_template} {self.collection.promotion}",
        )

    def test_collection_data(self):
        self.assertIsNotNone(self.collection.album_template)
        self.assertIsNotNone(self.collection.promotion)

    def test_prize_creation(self):
        """Test that standard and surprise prizes are created correctly."""

        expected_standard_prizes = self.collection.album_template.layout.PAGES
        self.assertEqual(
            self.collection.standard_prizes.count(), expected_standard_prizes
        )

        for page in range(1, self.collection.album_template.layout.PAGES + 1):
            self.assertTrue(self.collection.standard_prizes.filter(page=page).exists())

        expected_surprise_prizes = (
            self.collection.album_template.layout.SURPRISE_PRIZE_OPTIONS
        )
        self.assertEqual(
            self.collection.surprise_prizes.count(), expected_surprise_prizes
        )

        for number in range(
            1, self.collection.album_template.layout.SURPRISE_PRIZE_OPTIONS + 1
        ):
            self.assertTrue(
                self.collection.surprise_prizes.filter(number=number).exists()
            )

    def test_box_cost_property(self):
        """Test that box_cost property calculates correctly."""
        expected_cost = (
            self.promotion.pack_cost
            * self.collection.album_template.layout.PACKS_PER_BOX
        )
        self.assertEqual(self.collection.box_cost, expected_cost)

    def test_unique_constraint(self):
        """Test that unique constraint works."""
        with self.assertRaises(ValidationError):
            CollectionFactory(
                album_template=self.collection.album_template,
            )

    def test_get_random_surprise_prize(self):
        """Test that get_random_surprise_prize returns a valid surprise prize."""
        prize = self.collection.get_random_surprise_prize()
        self.assertIsNotNone(prize)
        self.assertTrue(
            prize.number
            in range(
                1, self.collection.album_template.layout.SURPRISE_PRIZE_OPTIONS + 1
            )
        )

    def test_no_promotion_error(self):
        """Test that creating a collection without an active promotion raises an error."""
        # Delete all promotions
        Promotion.objects.all().delete()

        with self.assertRaises(ValidationError):
            CollectionFactory(album_template__name="Mario")

    def test_album_template_protection(self):
        with self.assertRaises(ProtectedError):
            self.collection.album_template.delete()

    def test_promotion_cascade(self):
        promotion_id = self.collection.promotion.id
        self.collection.promotion.delete()
        self.assertFalse(Collection.objects.filter(promotion_id=promotion_id).exists())

    def test_no_current_promotion(self):
        Promotion.objects.all().delete()
        PromotionFactory(past=True)
        collection = CollectionFactory.build(album_template__name="Angela")

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
