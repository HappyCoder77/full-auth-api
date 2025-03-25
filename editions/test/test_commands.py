from io import StringIO
from unittest.mock import patch, MagicMock
from decimal import Decimal

from django.test import TestCase
from django.core.management import call_command
from django.core.exceptions import ValidationError

from collection_manager.models import Collection
from ..models import Edition
from .factories import EditionFactory
from collection_manager.test.factories import CollectionFactory
from promotions.test.factories import PromotionFactory


class HandleEditionsCommandTest(TestCase):
    def setUp(self):
        self.out = StringIO()
        self.promotion = PromotionFactory()
        self.collection = CollectionFactory(
            album_template__with_coordinate_images=True, with_prizes_defined=True
        )

    def test_create_edition_success(self):
        """Test successful edition creation"""
        with patch("builtins.input", return_value="yes"):
            call_command(
                "handle_editions",
                "create",
                collection=self.collection.id,
                circulation=1,
                stdout=self.out,
            )

        # Check output
        output = self.out.getvalue()
        self.assertIn("Edition created successfully", output)

        # Check database
        self.assertEqual(Edition.objects.count(), 1)
        edition = Edition.objects.first()
        self.assertEqual(edition.collection, self.collection)
        self.assertEqual(edition.circulation, Decimal("1"))

    def test_create_edition_cancelled(self):
        """Test cancellation of edition creation"""
        with patch("builtins.input", return_value="no"):
            call_command(
                "handle_editions",
                "create",
                collection=self.collection.id,
                circulation=100,
                stdout=self.out,
            )

        # Check output
        output = self.out.getvalue()
        self.assertIn("Operation cancelled", output)

        # Check database
        self.assertEqual(Edition.objects.count(), 0)

    def test_create_edition_validation_error(self):
        """Test handling of validation errors"""
        # Create a collection without prize descriptions
        collection = CollectionFactory(
            album_template__with_coordinate_images=True, album_template__name="Angela"
        )

        call_command(
            "handle_editions",
            "create",
            collection=collection.id,
            circulation=1,
            stdout=self.out,
        )

        # Check output
        output = self.out.getvalue()
        self.assertIn("Validation error", output)

        # Check database
        self.assertEqual(Edition.objects.count(), 0)

    def test_create_edition_nonexistent_collection(self):
        """Test handling of nonexistent collection"""
        call_command(
            "handle_editions",
            "create",
            collection=999,
            circulation=1,
            stdout=self.out,
        )

        # Check output
        output = self.out.getvalue()
        self.assertIn("Collection with ID 999 does not exist", output)

        # Check database
        self.assertEqual(Edition.objects.count(), 0)

    def test_delete_edition_success(self):
        """Test successful edition deletion"""
        edition = EditionFactory(collection=self.collection)

        with patch("builtins.input", return_value="y"):
            call_command("handle_editions", "delete", edition.id, stdout=self.out)

        # Check output
        output = self.out.getvalue()
        self.assertIn(f"Edition {edition.id} successfully deleted", output)

        # Check database
        self.assertEqual(Edition.objects.count(), 0)

    def test_delete_edition_cancelled(self):
        """Test cancellation of edition deletion"""
        edition = EditionFactory(collection=self.collection)

        with patch("builtins.input", return_value="n"):
            call_command("handle_editions", "delete", edition.id, stdout=self.out)

        # Check output
        output = self.out.getvalue()
        self.assertIn("Operation cancelled", output)

        # Check database
        self.assertEqual(Edition.objects.count(), 1)

    def test_delete_nonexistent_edition(self):
        """Test handling of nonexistent edition"""
        call_command("handle_editions", "delete", 999, stdout=self.out)

        # Check output
        output = self.out.getvalue()
        self.assertIn("Edition with ID 999 does not exist", output)
