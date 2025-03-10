from django.test import TestCase
from django.contrib.auth import get_user_model


from promotions.test.factories import PromotionFactory
from ..models import StandardPrize, Collection
from ..serializers import StandardPrizeSerializer
from .factories import CollectionFactory

User = get_user_model()


class StandardPrizeSerializerTest(TestCase):
    def setUp(self):
        PromotionFactory()
        self.collection = CollectionFactory()

        self.prize = StandardPrize.objects.get(page=1)
        self.serializer = StandardPrizeSerializer(instance=self.prize)

    def test_contains_expected_fields(self):
        data = self.serializer.data
        expected_fields = {"id", "collection", "collection_name", "page", "description"}
        self.assertEqual(set(data.keys()), expected_fields)

    def test_collection_name_field_content(self):
        data = self.serializer.data
        self.assertEqual(data["collection_name"], "Minecraft")

    def test_page_field_content(self):
        data = self.serializer.data
        self.assertEqual(data["page"], 1)
