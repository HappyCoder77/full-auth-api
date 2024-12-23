from rest_framework import serializers
from rest_framework.test import APITestCase
from promotions.test.factories import PromotionFactory
from editions.test.factories import EditionFactory
from authentication.test.factories import UserFactory
from users.test.factories import DealerFactory
from commerce.models import Order
from commerce.serializers import OrderSerializer


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
