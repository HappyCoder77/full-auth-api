
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
            dealer=cls.dealer, edition=cls.edition)
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


class OrderTestCase(TestCase):

    def setUp(self):
        self.promotion = PromotionFactory()
        self.edition = EditionFactory(promotion=self.promotion)
        self.dealer = UserFactory()

    def test_order_data(self):
        # TODO: eliminar tal vez el dealer ya que el factory lo agrega
        order = Orderfactory.build(
            dealer=self.dealer,
            edition=self.edition,
        )
        order.full_clean()
        order.save()
        amount = order.pack_cost * order.box.packs.all().count()
        self.assertEqual(order.date, NOW.date())
        self.assertEqual(order.box, self.edition.boxes.first())
        self.assertEqual(order.dealer, self.dealer)
        self.assertEqual(order.pack_cost, 1.5)
        self.assertEqual(
            order.__str__(), f'{order.id} / {order.date}')
        self.assertEqual(order.amount, amount)

    def test_create_order_without_current_promotion(self):
        self.promotion.delete()
        PromotionFactory(past=True)
        order = Orderfactory.build(
            dealer=self.dealer,
            edition=self.edition,
        )
        with self.assertRaises(ValidationError):
            order.full_clean()

    def test_create_order_with_invalid_edition(self):
        PromotionFactory(past=True)
        order = Orderfactory.build(
            dealer=self.dealer,
            edition_id=10000,
        )
        with self.assertRaises(ValidationError):
            order.full_clean()

    def test_create_order_without_available_box(self):
        Orderfactory(
            dealer=self.dealer,
            edition=self.edition,
        )

        order = Orderfactory.build(
            dealer=self.dealer,
            edition=self.edition,
        )

        with self.assertRaises(ValidationError):
            order.full_clean()
