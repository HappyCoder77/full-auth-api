from django.test import TestCase
from authentication.test.factories import UserFactory
from collection_manager.models import Coordinate, SurprisePrize
from promotions.test.factories import PromotionFactory
from users.test.factories import CollectorFactory
from ..serializers import PackSerializer, StickerPrizeSerializer, StickerSerializer
from ..test.factories import EditionFactory
from ..models import Pack, Sticker


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
            self.assertFalse(sticker["is_repeated"])
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


class StickerPrizeSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.promotion = PromotionFactory()
        cls.edition = EditionFactory(promotion=cls.promotion)
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

    def test_sticker_prize_serializer(self):
        serializer = StickerPrizeSerializer(instance=self.sticker_prize)
        data = serializer.data

        self.assertEqual(set(data.keys()), {"id", "prize", "claimed", "claimed_date"})
        self.assertEqual(data["id"], self.sticker_prize.id)
        self.assertEqual(
            data["prize"]["description"], self.sticker_prize.prize.description
        )
        self.assertEqual(data["claimed"], self.sticker_prize.claimed)
        self.assertEqual(data["claimed_date"], self.sticker_prize.claimed_date)

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


class StickerSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.promotion = PromotionFactory()
        cls.edition = EditionFactory(promotion=cls.promotion)
        cls.collector = CollectorFactory(user=UserFactory())
        cls.coordinate = Coordinate.objects.first()
        cls.sticker = Sticker.objects.filter(coordinate=cls.coordinate).first()

    def test_sticker_serializer_data(self):
        serializer = StickerSerializer(instance=self.sticker)
        data = serializer.data

        self.assertEqual(
            set(data.keys()),
            {
                "id",
                "ordinal",
                "number",
                "on_the_board",
                "is_repeated",
                "coordinate",
                "prize",
            },
        )
        self.assertEqual(data["id"], self.sticker.id)
        self.assertEqual(data["ordinal"], self.sticker.ordinal)
        self.assertEqual(data["number"], self.sticker.number)
        self.assertEqual(data["on_the_board"], self.sticker.on_the_board)
        self.assertEqual(data["is_repeated"], self.sticker.is_repeated)
        self.assertEqual(data["coordinate"]["id"], self.coordinate.id)
        self.assertEqual(
            data["coordinate"]["absolute_number"], self.coordinate.absolute_number
        )
        self.assertIsNone(data["coordinate"]["image"], self.coordinate.image)
        self.assertIsNone(data["prize"])
