
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from authentication.test.factories import UserFactory
from editions.test.factories import EditionFactory
from promotions.test.factories import PromotionFactory
from .factories import SaleFactory, Orderfactory

NOW = timezone.now()

# TODO: terminar...


class SaleTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.promotion = PromotionFactory()
        cls.edition = EditionFactory(promotion=cls.promotion)
        cls.dealer = UserFactory()
        cls.collector = UserFactory()
        cls.order = Orderfactory(
            dealer=cls.dealer, box=cls.edition.boxes.first())
        cls.sale = SaleFactory(date=NOW, edition=cls.edition,
                               dealer=cls.dealer, collector=cls.collector)

    def test_sale_data(self):
        self.assertEqual(self.sale.date, NOW)
        self.assertEqual(self.sale.edition, self.edition)
        self.assertEqual(self.sale.dealer, self.dealer)
        self.assertEqual(self.sale.collector, self.collector)
        self.assertEqual(self.sale.quantity, 1)
        self.assertEqual(self.sale.__str__(
        ), f'{self.sale.id} / {self.sale.date} / {self.sale.collector}')
        self.assertEqual(self.sale.collection, self.edition.collection)

    def test_validation_not_raised(self):
        self.sale.clean()

    def test_sale_validation(self):
        sale = SaleFactory(date=NOW, edition=self.edition,
                           dealer=self.dealer, collector=self.collector, quantity=15)

        with self.assertRaises(ValidationError) as context:
            sale.clean()

        error_messages = context.exception.messages
        self.assertTrue(
            any("Inventario insuficiente:" in message for message in error_messages))


class OrderTestcase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.promotion = PromotionFactory()
        cls.edition = EditionFactory(promotion=cls.promotion)
        cls.dealer = UserFactory()
        cls.order = Orderfactory(
            dealer=cls.dealer,
            date=NOW,
            box=cls.edition.boxes.first())

    def test_order_data(self):
        amount = self.order.pack_cost * self.order.box.packs.all().count()
        self.assertEqual(self.order.date, NOW)
        self.assertEqual(self.order.box, self.edition.boxes.first())
        self.assertEqual(self.order.dealer, self.dealer)
        self.assertEqual(self.order.pack_cost, 1.5)
        self.assertEqual(
            self.order.__str__(), f'{self.order.id} / {self.order.date}')
        self.assertEqual(self.order.amount, amount)
