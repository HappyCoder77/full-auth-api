from django.test import TestCase
from django.contrib.auth import get_user_model
from authentication.test.factories import UserFactory
from editions.models import Sticker
from editions.test.factories import EditionFactory
from promotions.test.factories import PromotionFactory
from .factories import CollectorFactory
from ..serializers import CollectorSerializer


class CollectorSerializerTest(TestCase):

    def setUp(self):
        self.collector = CollectorFactory(user=UserFactory())

    def test_serializer_contains_expected_fields(self):
        serializer = CollectorSerializer(instance=self.collector)
        expected_fields = {
            "id",
            "first_name",
            "middle_name",
            "last_name",
            "second_last_name",
            "gender",
            "birthdate",
            "email",
            "unclaimed_surprise_prizes",
        }
        self.assertEqual(set(serializer.data.keys()), expected_fields)

    def test_user_field_is_write_only(self):
        serializer = CollectorSerializer(instance=self.collector)
        self.assertNotIn("user", serializer.data)

    def test_unclaimed_surprise_prizes_serialization(self):
        serializer = CollectorSerializer(instance=self.collector)
        self.assertEqual(len(serializer.data["unclaimed_surprise_prizes"]), 0)

    def test_serializer_with_valid_data(self):
        user = UserFactory()
        valid_data = {
            "user": user.id,
            "first_name": "Jane",
            "last_name": "Smith",
            "email": user.email,
            "gender": "F",
            "birthdate": "1992-03-15",
        }
        serializer = CollectorSerializer(data=valid_data)

        self.assertTrue(serializer.is_valid())

    def test_serializer_with_invalid_data(self):
        invalid_data = {
            "first_name": "",
            "email": "invalid-email",
        }
        serializer = CollectorSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("first_name", serializer.errors)
        self.assertIn("email", serializer.errors)

    def test_serializer_with_suprise_prizes(self):
        EditionFactory(promotion=PromotionFactory())
        prized_sticker = Sticker.objects.filter(coordinate__absolute_number=0).first()
        prized_sticker.pack.open(self.collector.user)
        prized_sticker.refresh_from_db()
        stickerprize = prized_sticker.discover_prize()
        serializer = CollectorSerializer(instance=self.collector)
        expected_fields = {
            "id",
            "first_name",
            "middle_name",
            "last_name",
            "second_last_name",
            "gender",
            "birthdate",
            "email",
            "unclaimed_surprise_prizes",
        }

        self.assertEqual(set(serializer.data.keys()), expected_fields)
        self.assertEqual(len(serializer.data["unclaimed_surprise_prizes"]), 1)
        self.assertEqual(
            serializer.data["unclaimed_surprise_prizes"][0]["id"], stickerprize.id
        )
        self.assertEqual(
            serializer.data["unclaimed_surprise_prizes"][0]["prize"]["description"],
            stickerprize.prize.description,
        )
        self.assertEqual(
            serializer.data["unclaimed_surprise_prizes"][0]["claimed"],
            stickerprize.claimed,
        )
        self.assertEqual(
            serializer.data["unclaimed_surprise_prizes"][0]["claimed_date"],
            stickerprize.claimed_date,
        )
        self.assertEqual(
            serializer.data["unclaimed_surprise_prizes"][0]["claimed_by"],
            stickerprize.claimed_by,
        )
