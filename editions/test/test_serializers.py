from django.test import TestCase
from authentication.test.factories import UserFactory
from promotions.test.factories import PromotionFactory
from users.test.factories import CollectorFactory
from ..serializers import PackSerializer
from ..test.factories import EditionFactory
from ..models import Pack


class PackSerializerTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.promotion = PromotionFactory()
        cls.edition = EditionFactory(promotion=cls.promotion)
        cls.collector = CollectorFactory(user=UserFactory())
        cls.pack = Pack.objects.first()

    def test_pack_serialization(self):
        serializer = PackSerializer(instance=self.pack)
        data = serializer.data
        stickers_data = serializer.data["stickers"]

        self.assertEqual(data["id"], self.pack.id)
        self.assertIsNone(data["collector"])
        self.assertEqual(data["is_open"], False)
        self.assertTrue("stickers" in data)
        self.assertEqual(len(data["stickers"]), 3)

        for sticker in stickers_data:
            coordinate_data = sticker["coordinate"]

            self.assertIn("id", sticker)
            self.assertIn("coordinate", sticker)
            self.assertIn("ordinal", sticker)
            self.assertIn("number", sticker)
            self.assertIn("on_the_board", sticker)
            self.assertIsInstance(sticker["id"], int)
            self.assertIsInstance(sticker["ordinal"], int)
            self.assertIsInstance(sticker["on_the_board"], bool)
            self.assertIn("id", coordinate_data)
            self.assertIn("absolute_number", coordinate_data)
            self.assertIn("image", coordinate_data)
            self.assertIsInstance(coordinate_data["id"], int)
            self.assertIsInstance(coordinate_data["absolute_number"], int)
            self.assertIsNone(coordinate_data["image"])

    def test_serializer_expected_fields(self):
        serializer = PackSerializer(instance=self.pack)
        expected_fields = {"id", "collector", "is_open", "stickers"}

        self.assertEqual(set(serializer.data.keys()), expected_fields)
