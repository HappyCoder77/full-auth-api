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

        self.assertEqual(data["id"], self.pack.id)
        self.assertIsNone(data["collector"])
        self.assertEqual(data["is_open"], False)
