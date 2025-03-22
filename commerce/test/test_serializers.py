import os
import shutil
from django.test.utils import override_settings
import tempfile

from rest_framework import serializers
from rest_framework.test import APITestCase, APIRequestFactory
from promotions.test.factories import PromotionFactory
from rest_framework.exceptions import ValidationError
from editions.test.factories import EditionFactory
from authentication.test.factories import UserFactory
from users.test.factories import DealerFactory, CollectorFactory
from collection_manager.test.factories import CollectionFactory
from commerce.test.factories import OrderFactory
from commerce.models import Order, Box, Pack, Edition, Sale
from commerce.serializers import OrderSerializer, SaleSerializer
from django.utils import timezone

TEMP_MEDIA_ROOT = tempfile.mkdtemp()


# TODO: Add tests for the rest of the serializers
@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class OrderSerializerTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.promotion = PromotionFactory()
        collection = CollectionFactory(
            album_template__with_coordinate_images=True, with_prizes_defined=True
        )
        cls.edition = EditionFactory(collection=collection)
        cls.user_dealer = UserFactory()
        cls.dealer = DealerFactory(user=cls.user_dealer)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_order_serialization(self):
        order = Order.objects.create(
            dealer=self.dealer.user,
            collection=self.edition.collection,
        )

        serializer = OrderSerializer(order)
        data = serializer.data

        self.assertEqual(data["id"], order.id)
        self.assertEqual(data["dealer"], order.dealer.id)
        self.assertEqual(data["date"], str(order.date))
        self.assertEqual(data["collection"], order.collection.id)
        self.assertEqual(data["box"], order.box.id)
        self.assertEqual(data["pack_cost"], str(order.pack_cost))
        self.assertEqual(data["amount"], str(order.amount))

    def test_order_deserialization(self):
        data = {
            "collection": self.edition.collection.id,
        }
        serializer = OrderSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        order = serializer.save(dealer=self.dealer.user)

        self.assertEqual(order.dealer, self.dealer.user)
        self.assertEqual(order.collection, self.edition.collection)
        self.assertEqual(order.box, self.edition.boxes.first())
        self.assertEqual(order.pack_cost, self.edition.collection.promotion.pack_cost)

    def test_order_validation(self):
        data = {
            "collection": 99999,  # Invalid edition ID
        }
        serializer = OrderSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("collection", serializer.errors)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class SaleSerializerTestCase(APITestCase):
    def setUp(self):
        PromotionFactory()
        collection = CollectionFactory(
            album_template__with_coordinate_images=True, with_prizes_defined=True
        )
        self.edition = EditionFactory(collection=collection)
        self.dealer = DealerFactory(user=UserFactory())
        self.collector = CollectorFactory(user=UserFactory())
        self.order = OrderFactory(
            dealer=self.dealer.user, collection=self.edition.collection
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_serialization(self):
        sale = Sale.objects.create(
            date=timezone.now().date(),
            collection=self.edition.collection,
            dealer=self.dealer.user,
            collector=self.collector.user,
            quantity=1,
        )

        serializer = SaleSerializer(sale)
        serialized_data = serializer.data

        self.assertIn("id", serialized_data)
        self.assertIn("date", serialized_data)
        self.assertEqual(serialized_data["collection"], self.edition.collection.id)
        self.assertEqual(
            serialized_data["collection_name"],
            self.edition.collection.album_template.name,
        )
        self.assertEqual(serialized_data["dealer"], self.dealer.user.id)
        self.assertEqual(serialized_data["dealer_name"], self.dealer.get_full_name)
        self.assertEqual(serialized_data["collector"], self.collector.user.id)
        self.assertEqual(
            serialized_data["collector_name"], self.collector.get_full_name
        )
        self.assertEqual(serialized_data["quantity"], 1)

    def test_input_validation(self):
        data = {
            "collection": self.edition.collection.id,
            "collector": self.collector.id,
            "quantity": 1,
        }

        request = APIRequestFactory().get("/")
        request.user = self.dealer.user
        serializer = SaleSerializer(data=data, context={"request": request})
        serializer.is_valid()
        serialized_data = serializer.validated_data
        self.assertEqual(serialized_data["collection"].id, self.edition.collection.id)
        self.assertEqual(serialized_data["collector"].id, self.collector.id)
        self.assertEqual(serialized_data["quantity"], 1)

    def test_insufficient_packs(self):
        Order.objects.all().delete()
        data = {
            "collection": self.edition.collection.id,
            "collector": self.collector.id,
            "quantity": 10,
        }

        request = APIRequestFactory().get("/")
        request.user = self.dealer.user
        serializer = SaleSerializer(data=data, context={"request": request})

        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)
