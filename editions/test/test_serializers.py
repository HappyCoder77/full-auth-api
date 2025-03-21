import os
import shutil
from django.test.utils import override_settings
import tempfile
from django.test import TestCase
from authentication.test.factories import UserFactory
from collection_manager.models import Coordinate, SurprisePrize
from promotions.test.factories import PromotionFactory
from users.test.factories import CollectorFactory
from ..serializers import PackSerializer, StickerPrizeSerializer, StickerSerializer
from ..test.factories import EditionFactory, CollectionFactory
from ..models import Pack, Sticker

TEMP_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PackSerializerTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        PromotionFactory()
        collection = CollectionFactory(album_template__with_coordinate_images=True)

        for prize in collection.surprise_prizes.all():
            prize.description = "Test prize"
            prize.save()

        for prize in collection.standard_prizes.all():
            prize.description = "Test prize"
            prize.save()

        cls.edition = EditionFactory(
            collection=collection,
        )
        cls.collector = CollectorFactory(user=UserFactory())
        cls.pack = Pack.objects.first()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

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
            self.assertFalse(sticker["is_repeated"])
            self.assertIsInstance(sticker["id"], int)
            self.assertIsInstance(sticker["ordinal"], int)
            self.assertIsInstance(sticker["on_the_board"], bool)
            self.assertIn("id", coordinate_data)
            self.assertIn("absolute_number", coordinate_data)
            self.assertIn("image", coordinate_data)
            self.assertIsInstance(coordinate_data["id"], int)
            self.assertIsInstance(coordinate_data["absolute_number"], int)
            self.assertIsNotNone(coordinate_data["image"])

    def test_serializer_expected_fields(self):
        serializer = PackSerializer(instance=self.pack)
        expected_fields = {"id", "collector", "is_open", "stickers"}

        self.assertEqual(set(serializer.data.keys()), expected_fields)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class StickerPrizeSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        PromotionFactory()
        collection = CollectionFactory(album_template__with_coordinate_images=True)
        for prize in collection.surprise_prizes.all():
            prize.description = "Test prize"
            prize.save()

        for prize in collection.standard_prizes.all():
            prize.description = "Test prize"
            prize.save()

        cls.edition = EditionFactory(collection=collection)
        cls.collector = CollectorFactory(user=UserFactory())

        # Get a prize sticker and create a prize for it
        cls.prize_sticker = Sticker.objects.filter(
            coordinate__absolute_number=0, pack__box__edition=cls.edition
        ).first()
        cls.pack = cls.prize_sticker.pack
        cls.pack.open(cls.collector.user)
        cls.sticker_prize = cls.prize_sticker.discover_prize()
        cls.surprise_prize = SurprisePrize.objects.filter(
            description=cls.sticker_prize.prize.description
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_sticker_prize_serializer(self):
        serializer = StickerPrizeSerializer(instance=self.sticker_prize)
        data = serializer.data

        self.assertEqual(
            set(data.keys()),
            {
                "id",
                "prize",
                "claimed",
                "claimed_date",
                "claimed_by",
                "status",
                "status_display",
            },
        )
        self.assertEqual(data["id"], self.sticker_prize.id)
        self.assertEqual(
            data["prize"]["description"], self.sticker_prize.prize.description
        )
        self.assertEqual(data["claimed"], self.sticker_prize.claimed)
        self.assertEqual(data["claimed_date"], self.sticker_prize.claimed_date)
        self.assertEqual(data["claimed_by"], self.sticker_prize.claimed_by)

    def test_sticker_serializer_with_prize(self):
        serializer = StickerSerializer(instance=self.prize_sticker)
        data = serializer.data

        self.assertIn("prize", data)
        self.assertEqual(data["prize"]["id"], self.sticker_prize.id)
        self.assertEqual(
            data["prize"]["prize"]["description"], self.sticker_prize.prize.description
        )

    def test_sticker_serializer_without_prize(self):
        regular_sticker = Sticker.objects.filter(
            coordinate__absolute_number__gt=0
        ).first()
        serializer = StickerSerializer(instance=regular_sticker)

        self.assertIsNone(serializer.data["prize"])


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class StickerSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        PromotionFactory()
        collection = CollectionFactory(album_template__with_coordinate_images=True)
        for prize in collection.surprise_prizes.all():
            prize.description = "Test prize"
            prize.save()

        for prize in collection.standard_prizes.all():
            prize.description = "Test prize"
            prize.save()

        cls.edition = EditionFactory(collection=collection)
        cls.collector = CollectorFactory(user=UserFactory())
        cls.coordinate = (
            Coordinate.objects.filter(rarity_factor__gte=1)
            .order_by("absolute_number")
            .first()
        )
        cls.sticker = Sticker.objects.filter(coordinate=cls.coordinate).first()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_sticker_serializer_data(self):
        serializer = StickerSerializer(instance=self.sticker)
        data = serializer.data
        expected_serializer_data = {
            "id": self.sticker.id,
            "ordinal": self.sticker.ordinal,
            "number": self.sticker.number,
            "on_the_board": self.sticker.on_the_board,
            "is_repeated": self.sticker.is_repeated,
            "is_rescued": self.sticker.is_rescued,
            "coordinate": {
                "id": self.coordinate.id,
                "absolute_number": self.coordinate.absolute_number,
                "image": self.coordinate.image.url,
            },
            "prize": None,
            "has_prize_discovered": hasattr(self.sticker, "prize"),
        }

        self.assertEqual(data, expected_serializer_data)
