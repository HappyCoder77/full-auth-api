from django.test import TestCase
from django.contrib.auth import get_user_model
from ..models import StandardPrize, OldCollection
from ..serializers import StandardPrizeSerializer

User = get_user_model()


class StandardPrizeSerializerTest(TestCase):
    def setUp(self):
        self.collection = OldCollection.objects.create(name="Test Collection")
        self.prize_data = {
            "collection": self.collection,
            "page": 1,
            "description": "Test Prize",
        }

        self.prize = StandardPrize.objects.create(**self.prize_data)
        self.serializer = StandardPrizeSerializer(instance=self.prize)

    def test_contains_expected_fields(self):
        data = self.serializer.data
        expected_fields = {"id", "collection", "collection_name", "page", "description"}
        self.assertEqual(set(data.keys()), expected_fields)

    def test_collection_name_field_content(self):
        data = self.serializer.data
        self.assertEqual(data["collection_name"], "Test Collection")

    def test_page_field_content(self):
        data = self.serializer.data
        self.assertEqual(data["page"], 1)
