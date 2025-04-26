import os
import shutil
from django.test.utils import override_settings
import tempfile


from datetime import date
from rest_framework.test import APITestCase
from django.test import TestCase


from authentication.test.factories import UserFactory
from editions.models import Pack
from editions.test.factories import EditionFactory
from collection_manager.models import StandardPrize
from collection_manager.test.factories import CollectionFactory
from promotions.test.factories import PromotionFactory
from users.test.factories import CollectorFactory

from ..serializers import (
    AlbumSerializer,
    SlotSerializer,
    PagePrizeSerializer,
    PageSerializer,
)
from ..models import Album, Slot, Page, PagePrize
from .factories import AlbumFactory

TEMP_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class AlbumSerializerTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        PromotionFactory()
        collection = CollectionFactory(
            album_template__with_coordinate_images=True,
            album_template__with_image=True,
            with_prizes_defined=True,
        )
        EditionFactory(collection=collection)
        cls.collector = CollectorFactory(user=UserFactory())
        cls.album = Album.objects.create(
            collector=cls.collector.user, collection=collection
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_serializer_contains_expected_fields(self):
        serializer = AlbumSerializer(instance=self.album)
        print(serializer.data)
        expected_fields = {
            "id",
            "collection",
            "collector",
            "pages",
            "pack_inbox",
            "stickers_on_the_board",
            "prized_stickers",
            "image",
        }

        self.assertEqual(set(serializer.data.keys()), expected_fields)
        self.assertIsNone(serializer.data["pack_inbox"])
        self.assertIsNone(serializer.data["stickers_on_the_board"])
        self.assertQuerySetEqual(serializer.data["prized_stickers"], [])

    def test_pages_serialization(self):
        serializer = AlbumSerializer(instance=self.album)
        self.assertEqual(
            len(serializer.data["pages"]),
            self.album.collection.album_template.layout.PAGES,
        )

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
        self.assertEqual(serializer.data["collection"], self.album.collection.id)


class SlotSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        PromotionFactory()
        cls.album = AlbumFactory()
        cls.slots = Slot.objects.all().order_by("id")

    def test_slot_data(self):
        expected_fields = {"id", "number", "absolute_number", "image", "is_empty"}

        absolute_counter = 1
        page_counter = 1
        for each_page in self.album.pages.all():
            slot_counter = 1

            for each_slot in each_page.slots.all():
                serializer = SlotSerializer(instance=each_slot)
                self.assertEqual(set(serializer.data.keys()), expected_fields)
                self.assertEqual(serializer.data["number"], slot_counter)
                self.assertEqual(serializer.data["absolute_number"], absolute_counter)
                self.assertIsNone(serializer.data["image"])
                self.assertTrue(serializer.data["is_empty"])

                slot_counter += 1
                absolute_counter += 1

            page_counter += 1


class PagePrizeSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        PromotionFactory()
        cls.album = AlbumFactory()
        page = Page.objects.first()
        prize = StandardPrize.objects.get(
            collection=cls.album.collection, page=page.number
        )
        cls.page_prize = PagePrize(page=page, prize=prize)
        PagePrize.objects.bulk_create([cls.page_prize], ignore_conflicts=True)
        cls.serializer = PagePrizeSerializer(instance=cls.page_prize)

    def test_page_prize_data(self):
        expected_fields = {
            "id",
            "page",
            "prize",
            "claimed_by",
            "claimed_date",
            "status",
            "status_display",
        }
        expected_prize_fields = {
            "id",
            "collection",
            "collection_name",
            "page",
            "description",
        }
        serialized_data = self.serializer.data
        self.assertEqual(set(serialized_data.keys()), expected_fields)
        self.assertEqual(set(serialized_data["prize"].keys()), expected_prize_fields)
        self.assertEqual(serialized_data["page"], self.page_prize.page.id)
        self.assertEqual(serialized_data["prize"]["id"], self.page_prize.prize.id)
        self.assertEqual(
            serialized_data["prize"]["collection"], self.page_prize.prize.collection.id
        )
        self.assertEqual(
            serialized_data["prize"]["collection_name"],
            self.page_prize.prize.collection.album_template.name,
        )
        self.assertEqual(serialized_data["prize"]["page"], self.page_prize.prize.page)
        self.assertEqual(
            serialized_data["prize"]["description"], self.page_prize.prize.description
        )

        self.assertIsNone(serialized_data["claimed_by"])
        self.assertIsNone(serialized_data["claimed_date"])


class PageSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        PromotionFactory()
        cls.album = AlbumFactory()

    def test_page_serializer_test_data(self):
        expected_fields = {
            "id",
            "page_prize",
            "number",
            "slots",
            "is_full",
            "prize_was_claimed",
        }

        page_counter = 1
        for each_page in self.album.pages.all():
            serializer = PageSerializer(instance=each_page)

            self.assertEqual(set(serializer.data.keys()), expected_fields)
            self.assertIsNone(serializer.data["page_prize"])
            self.assertEqual(serializer.data["number"], page_counter)
            self.assertFalse(serializer.data["is_full"])
            self.assertFalse(serializer.data["prize_was_claimed"])
            page_counter += 1
