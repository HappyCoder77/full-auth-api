from rest_framework import serializers
from rest_framework.test import APITestCase, APIRequestFactory
from promotions.test.factories import PromotionFactory
from rest_framework.exceptions import ValidationError
from editions.test.factories import EditionFactory
from authentication.test.factories import UserFactory
from users.test.factories import DealerFactory, CollectorFactory
from commerce.test.factories import OrderFactory
from commerce.models import Order, Box, Pack, Edition, Sale
from commerce.serializers import OrderSerializer, SaleSerializer
from django.utils import timezone


# TODO: Add tests for the rest of the serializers
class OrderSerializerTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.promotion = PromotionFactory()
        cls.user_dealer = UserFactory()
        cls.dealer = DealerFactory(user=cls.user_dealer)

    def test_order_serialization(self):
        edition = EditionFactory(promotion=self.promotion)
        order = Order.objects.create(
            dealer=self.dealer.user,
            edition=edition,
        )

        serializer = OrderSerializer(order)
        data = serializer.data

        self.assertEqual(data["id"], order.id)
        self.assertEqual(data["dealer"], order.dealer.id)
        self.assertEqual(data["date"], str(order.date))
        self.assertEqual(data["edition"], order.edition.id)
        self.assertEqual(data["box"], order.box.id)
        self.assertEqual(data["pack_cost"], str(order.pack_cost))
        self.assertEqual(data["amount"], str(order.amount))

    def test_order_deserialization(self):
        edition = EditionFactory(promotion=self.promotion)
        data = {
            "edition": edition.id,
        }
        serializer = OrderSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        order = serializer.save(dealer=self.dealer.user)

        self.assertEqual(order.dealer, self.dealer.user)
        self.assertEqual(order.edition, edition)
        self.assertEqual(order.box, edition.boxes.first())
        self.assertEqual(order.pack_cost, edition.promotion.pack_cost)

    def test_order_validation(self):
        data = {
            "edition": 99999,  # Invalid edition ID
        }
        serializer = OrderSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("edition", serializer.errors)


class SaleSerializerTestCase(APITestCase):
    def setUp(self):
        self.dealer = DealerFactory(user=UserFactory())
        self.collector = CollectorFactory(user=UserFactory())
        self.edition = EditionFactory(promotion=PromotionFactory())
        self.order = OrderFactory(dealer=self.dealer.user, edition=self.edition)

    def test_serialization(self):
        sale = Sale.objects.create(
            date=timezone.now().date(),
            edition=self.edition,
            dealer=self.dealer.user,
            collector=self.collector.user,
            quantity=1,
        )

        serializer = SaleSerializer(sale)
        serialized_data = serializer.data

        self.assertIn("id", serialized_data)
        self.assertIn("date", serialized_data)
        self.assertEqual(serialized_data["edition"], self.edition.id)
        self.assertEqual(serialized_data["edition_name"], self.edition.collection.name)
        self.assertEqual(serialized_data["dealer"], self.dealer.user.id)
        self.assertEqual(serialized_data["dealer_name"], self.dealer.get_full_name)
        self.assertEqual(serialized_data["collector"], self.collector.user.id)
        self.assertEqual(
            serialized_data["collector_name"], self.collector.get_full_name
        )
        self.assertEqual(serialized_data["quantity"], 1)

    def test_input_validation(self):
        data = {
            "edition": self.edition.id,
            "collector": self.collector.id,
            "quantity": 1,
        }

        request = APIRequestFactory().get("/")
        request.user = self.dealer.user
        serializer = SaleSerializer(data=data, context={"request": request})
        serializer.is_valid()
        serialized_data = serializer.validated_data
        self.assertEqual(serialized_data["edition"].id, self.edition.id)
        self.assertEqual(serialized_data["collector"].id, self.collector.id)
        self.assertEqual(serialized_data["quantity"], 1)

    def test_insufficient_packs(self):
        Order.objects.all().delete()
        data = {
            "edition": self.edition.id,
            "dealer": self.dealer.id,
            "collector": self.collector.id,
            "quantity": 10,
        }

        request = APIRequestFactory().get("/")
        request.user = self.dealer.user
        serializer = SaleSerializer(data=data, context={"request": request})

        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)
