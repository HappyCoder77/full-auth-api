from rest_framework.test import APITestCase

from authentication.test.factories import UserFactory
from editions.models import Pack
from editions.test.factories import EditionFactory
from promotions.test.factories import PromotionFactory
from users.test.factories import CollectorFactory

from ..serializers import AlbumSerializer
from ..models import Album


class AlbumSerializerTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.promotion = PromotionFactory()
        cls.edition = EditionFactory(promotion=cls.promotion)
        cls.collector = CollectorFactory(user=UserFactory())
        cls.album = Album.objects.create(
            collector=cls.collector.user, edition=cls.edition
        )

    def test_serializer_contains_expected_fields(self):
        serializer = AlbumSerializer(instance=self.album)
        expected_fields = {"id", "edition", "collector", "pages", "pack_inbox"}

        self.assertEqual(set(serializer.data.keys()), expected_fields)
        self.assertIsNone(serializer.data["pack_inbox"])

    def test_pages_serialization(self):
        serializer = AlbumSerializer(instance=self.album)
        self.assertEqual(len(serializer.data["pages"]), self.edition.collection.PAGES)

    def test_pack_inbox_serialization(self):
        pack = Pack.objects.first()
        pack.collector = self.collector.user
        pack.save()
        serializer = AlbumSerializer(instance=self.album)
        self.assertEqual(len(serializer.data["pack_inbox"]), 1)
        self.assertEqual(serializer.data["pack_inbox"][0]["id"], pack.id)
        self.assertFalse(serializer.data["pack_inbox"][0]["is_open"])
        self.assertEqual(
            serializer.data["pack_inbox"][0]["collector"], self.collector.user.id
        )

    def test_collector_serialization(self):
        serializer = AlbumSerializer(instance=self.album)
        self.assertEqual(serializer.data["collector"], self.collector.user.id)

    def test_edition_serialization(self):
        serializer = AlbumSerializer(instance=self.album)
        self.assertEqual(serializer.data["edition"], self.edition.id)
