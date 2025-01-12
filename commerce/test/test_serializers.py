from rest_framework import serializers
from rest_framework.test import APITestCase
from promotions.test.factories import PromotionFactory
from rest_framework.exceptions import ValidationError
from editions.test.factories import EditionFactory
from authentication.test.factories import UserFactory
from users.test.factories import DealerFactory, CollectorFactory
from commerce.test.factories import OrderFactory
from commerce.models import Order, Box, Pack, Edition
from commerce.serializers import OrderSerializer, SaleSerializer


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

    def test_valid_sale_serialization(self):
        data = {
            "edition": self.edition.id,
            "dealer": self.dealer.id,
            "collector": self.collector.id,
            "quantity": 1,
        }
        serializer = SaleSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_insufficient_packs(self):
        Order.objects.all().delete()
        data = {
            "edition": self.edition.id,
            "dealer": self.dealer.id,
            "collector": self.collector.id,
            "quantity": 10,
        }
        serializer = SaleSerializer(data=data)
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)
