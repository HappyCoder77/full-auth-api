from django.test import TestCase
from django.contrib.auth import get_user_model
from albums.models import Page, Pack
from albums.test.factories import AlbumFactory
from authentication.test.factories import UserFactory
from collection_manager.models import Coordinate
from collection_manager.test.factories import CollectionFactory
from editions.models import Sticker
from editions.test.factories import EditionFactory
from promotions.test.factories import PromotionFactory
from .factories import CollectorFactory, DealerFactory
from ..serializers import CollectorSerializer


class CollectorSerializerTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        collection = CollectionFactory()
        coordinate = Coordinate.objects.get(rarity_factor=0.02)
        coordinate.rarity_factor = 1
        coordinate.save()
        cls.user = UserFactory()
        cls.dealer = DealerFactory(user=UserFactory())
        cls.collector = CollectorFactory(user=cls.user, email=cls.user.email)
        cls.album = AlbumFactory(
            collector=cls.collector.user, edition__collection=collection
        )
        cls.page = Page.objects.get(number=1)
        cls.packs = Pack.objects.all()

        for pack in cls.packs:
            pack.open(cls.album.collector)

        stickers = Sticker.objects.filter(
            on_the_board=True, coordinate__absolute_number__lte=6
        )

        for slot in cls.page.slots.all():
            sticker = stickers.get(coordinate__absolute_number=slot.absolute_number)
            slot.place_sticker(sticker)

    def test_serializer_contains_expected_fields(self):
        serializer = CollectorSerializer(instance=self.collector)
        expected_fields = {
            "id",
            "user_id",
            "first_name",
            "middle_name",
            "last_name",
            "second_last_name",
            "full_name",
            "gender",
            "birthdate",
            "email",
            "unclaimed_surprise_prizes",
            "unclaimed_page_prizes",
        }
        self.assertEqual(set(serializer.data.keys()), expected_fields)

    def test_user_field_is_write_only(self):
        serializer = CollectorSerializer(instance=self.collector)
        self.assertNotIn("user", serializer.data)

    def test_unclaimed_surprise_prizes_serialization(self):
        serializer = CollectorSerializer(instance=self.collector)
        self.assertEqual(len(serializer.data["unclaimed_surprise_prizes"]), 0)

    def test_unclaimed_page_prizes_serialization(self):
        serializer = CollectorSerializer(instance=self.collector)
        self.assertEqual(len(serializer.data["unclaimed_page_prizes"]), 0)

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
        prized_sticker = Sticker.objects.filter(coordinate__absolute_number=0).first()
        prized_sticker.pack.open(self.collector.user)
        prized_sticker.refresh_from_db()
        stickerprize = prized_sticker.discover_prize()
        serializer = CollectorSerializer(instance=self.collector)
        expected_fields = {
            "id",
            "user_id",
            "first_name",
            "middle_name",
            "last_name",
            "second_last_name",
            "full_name",
            "gender",
            "birthdate",
            "email",
            "unclaimed_surprise_prizes",
            "unclaimed_page_prizes",
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

    def test_serializer_data_with_unclaimed_page_prizes(self):
        page_prize = self.page.create_prize()

        self.assertEqual(self.collector.unclaimed_page_prizes.count(), 1)
        self.assertEqual(self.collector.unclaimed_page_prizes[0].id, page_prize.id)
        self.assertEqual(self.collector.unclaimed_page_prizes[0].page, page_prize.page)
        self.assertEqual(
            self.collector.unclaimed_page_prizes[0].prize, page_prize.prize
        )
        self.assertEqual(
            self.collector.unclaimed_page_prizes[0].prize.description,
            page_prize.prize.description,
        )
        self.assertFalse(self.collector.unclaimed_page_prizes[0].claimed)
        self.assertIsNone(
            self.collector.unclaimed_page_prizes[0].claimed_date,
        )
        self.assertIsNone(
            self.collector.unclaimed_page_prizes[0].claimed_by,
        )

        self.assertEqual(self.collector.unclaimed_page_prizes[0].status, 1)
