import os
from decimal import Decimal
from datetime import datetime, timedelta, date
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from authentication.test.factories import UserFactory
from editions.test.factories import EditionFactory
from promotions.test.factories import PromotionFactory
from users.test.factories import DealerFactory

from ..models import Payment, MobilePayment, DealerBalance, Sale
from .factories import (
    SaleFactory,
    OrderFactory,
    PaymentFactory,
    MobilePaymentFactory,
    DealerBalanceFactory,
)


NOW = timezone.now()


class SaleTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.promotion = PromotionFactory()
        cls.edition = EditionFactory(promotion=cls.promotion)
        cls.user = UserFactory()
        cls.dealer = DealerFactory(user=cls.user, email=cls.user.email)
        cls.collector = UserFactory()
        cls.order = OrderFactory(dealer=cls.dealer.user, edition=cls.edition)
        cls.sale = SaleFactory(
            edition=cls.edition,
            dealer=cls.dealer.user,
            collector=cls.collector,
        )

    def test_sale_data(self):
        self.assertEqual(self.sale.date, date.today())
        self.assertEqual(self.sale.edition, self.edition)
        self.assertEqual(self.sale.dealer, self.dealer.user)
        self.assertEqual(self.sale.collector, self.collector)
        self.assertEqual(self.sale.quantity, 1)
        self.assertEqual(
            self.sale.__str__(),
            f"{self.sale.id} / {self.sale.date} / {self.sale.collector}",
        )
        self.assertEqual(self.sale.collection, self.edition.collection)
        self.assertEqual(self.sale.packs.count(), 1)

        for each_pack in self.sale.packs.all():
            self.assertEqual(each_pack.pack.collector, self.collector)
            self.assertFalse(each_pack.pack.is_open)

    def test_validation_not_raised(self):
        self.sale.clean()

    def test_sale_validation(self):
        sale = Sale(
            edition=self.edition,
            dealer=self.dealer.user,
            collector=self.collector,
            quantity=15,
        )

        with self.assertRaises(ValidationError) as context:
            sale.clean()

        error_messages = context.exception.messages
        self.assertTrue(
            any("Inventario insuficiente:" in message for message in error_messages)
        )


class OrderTestCase(TestCase):

    def setUp(self):
        self.promotion = PromotionFactory()
        self.edition = EditionFactory(promotion=self.promotion)
        self.user = UserFactory()
        self.dealer = DealerFactory(user=self.user, email=self.user.email)

    def tearDown(self):
        for payment in Payment.objects.all():
            payment.capture.delete(save=False)
            payment.delete()

    def test_order_data(self):
        # TODO: eliminar tal vez el dealer ya que el factory lo agrega
        order = OrderFactory.build(
            dealer=self.dealer.user,
            edition=self.edition,
        )
        order.full_clean()
        order.save()
        amount = order.pack_cost * order.box.packs.all().count()
        self.assertEqual(order.date, NOW.date())
        self.assertEqual(order.box, self.edition.boxes.first())
        self.assertEqual(order.dealer, self.dealer.user)
        self.assertEqual(order.pack_cost, 1.5)
        self.assertEqual(order.__str__(), f"{order.id} / {order.date}")
        self.assertEqual(order.amount, amount)

    def test_create_order_without_current_promotion(self):
        self.promotion.delete()
        PromotionFactory(past=True)
        order = OrderFactory.build(
            dealer=self.dealer.user,
            edition=self.edition,
        )
        with self.assertRaises(ValidationError):
            order.full_clean()

    def test_create_order_with_invalid_edition(self):
        PromotionFactory(past=True)
        order = OrderFactory.build(
            dealer=self.dealer.user,
            edition_id=10000,
        )
        with self.assertRaises(ValidationError):
            order.full_clean()

    def test_create_order_without_available_box(self):
        OrderFactory(
            dealer=self.dealer.user,
            edition=self.edition,
        )

        order = OrderFactory.build(
            dealer=self.dealer.user,
            edition=self.edition,
        )

        with self.assertRaises(ValidationError):
            order.full_clean()

    def test_create_order_with_existing_stock(self):
        # First order to create initial stock
        first_order = OrderFactory(
            dealer=self.dealer.user,
            edition=self.edition,
        )

        # Attempt to create second order while having stock
        second_order = OrderFactory.build(
            dealer=self.dealer.user,
            edition=self.edition,
        )

        with self.assertRaises(ValidationError) as context:
            second_order.full_clean()

        self.assertIn(
            "No puedes comprar mas sobres mientras tengas inventario disponible",
            str(context.exception),
        )

    def test_create_order_with_pending_balance(self):
        # Create dealer balance with pending amount
        DealerBalanceFactory(
            start_date=self.promotion.start_date,
            dealer=self.dealer.user,
            promotion=self.promotion,
            initial_balance=151,
        )

        order = OrderFactory.build(
            dealer=self.dealer.user,
            edition=self.edition,
        )

        with self.assertRaises(ValidationError) as context:
            order.full_clean()

        self.assertIn(
            "No puedes realizar nuevas compras mientras tengas saldo superior a 150.0 Bs.",
            str(context.exception),
        )

    def test_create_order_with_zero_balance(self):
        # Create dealer balance with zero balance
        balance = DealerBalanceFactory(
            start_date=self.promotion.start_date,
            dealer=self.dealer.user,
            promotion=self.promotion,
            initial_balance=0,
        )

        order = OrderFactory.build(
            dealer=self.dealer.user,
            edition=self.edition,
        )
        # Should not raise any validation errors
        order.full_clean()

    def test_create_order_with_negative_balance(self):
        # Create dealer balance with zero balance
        balance = DealerBalanceFactory(
            start_date=self.promotion.start_date,
            dealer=self.dealer.user,
            promotion=self.promotion,
            initial_balance=0,
        )
        PaymentFactory(
            dealer=self.dealer.user,
            amount=100,
            payment_date=self.promotion.start_date,
        )
        order = OrderFactory.build(
            dealer=self.dealer.user,
            edition=self.edition,
        )
        # Should not raise any validation errors
        order.full_clean()


class PaymentTestCase(TestCase):
    def setUp(self):
        self.user = UserFactory(email="testuser@example.com", password="12345")
        self.payment_data = {
            "status": "pending",
            "bank": "0134",
            "payment_type": "bank",
            "dealer": self.user,
            "amount": 100.50,
            "id_number": "12345678",
            "payment_date": "2024-07-05",
            "reference": "REF123456789",
            "capture": SimpleUploadedFile(
                "test_image.jpg", b"file_content", content_type="image/jpeg"
            ),
        }

    def tearDown(self):
        """Limpia los archivos de prueba después de cada test"""
        for payment in Payment.objects.all():
            if payment.capture and os.path.exists(payment.capture.path):
                try:
                    os.remove(payment.capture.path)
                except FileNotFoundError:
                    pass

    def test_payment_creation(self):
        payment = PaymentFactory()
        self.assertTrue(isinstance(payment, Payment))
        self.assertEqual(
            payment.__str__(),
            f"{payment.dealer.email} - {payment.amount} - {payment.date.date()} - {payment.status}",
        )
        self.assertEqual(payment.status, "pending")
        self.assertEqual(payment.payment_type, "bank")

    def test_custom_payment_creation(self):
        payment = PaymentFactory(**self.payment_data)

        self.assertEqual(
            payment.__str__(),
            f"{payment.dealer.email} - {payment.amount} - {payment.payment_date} - {payment.status}",
        )
        self.assertEqual(payment.status, "pending")
        self.assertEqual(payment.bank, "0134")
        self.assertEqual(payment.payment_type, "bank")
        self.assertEqual(payment.dealer, self.user)
        self.assertEqual(payment.amount, 100.50)
        self.assertEqual(payment.id_number, "12345678")
        self.assertEqual(payment.payment_date, "2024-07-05")

    def test_payment_status_choices(self):
        payment = PaymentFactory(**self.payment_data)
        self.assertIn(payment.status, dict(Payment.PAYMENT_STATUS))

    def test_payment_bank_choices(self):
        payment = PaymentFactory(**self.payment_data)
        self.assertIn(payment.bank, dict(Payment.BANKS))

    def test_payment_type_choices(self):
        payment = PaymentFactory(**self.payment_data)
        self.assertIn(payment.payment_type, dict(Payment.PAYMENT_TYPES))

    def test_invalid_id_number_too_short(self):
        self.payment_data["id_number"] = "123"
        with self.assertRaises(ValidationError):
            payment = PaymentFactory.build(**self.payment_data)
            payment.full_clean()

    def test_invalid_id_number_too_large(self):
        self.payment_data["id_number"] = "123456789"
        with self.assertRaises(ValidationError):
            payment = PaymentFactory.build(**self.payment_data)
            payment.full_clean()

    def test_invalid_id_number_not_numeric(self):
        self.payment_data["id_number"] = "abcdefgh"
        with self.assertRaises(ValidationError):
            payment = PaymentFactory.build(**self.payment_data)
            payment.full_clean()

    def test_valid_id_number(self):
        valid_id_numbers = ["1234567", "12345678"]
        for id_number in valid_id_numbers:
            self.payment_data["id_number"] = id_number
            payment = PaymentFactory.build(**self.payment_data)
            try:
                payment.full_clean()
            except ValidationError:
                self.fail(f"ValidationError raised with valid id_number: {id_number}")

    def test_amount_decimal_places_too_much(self):
        self.payment_data["amount"] = 100.555
        with self.assertRaises(ValidationError):
            payment = Payment(**self.payment_data)
            payment.full_clean()

    def test_payment_capture_upload(self):
        payment = PaymentFactory(**self.payment_data)

        self.assertTrue(payment.capture)
        self.assertTrue(payment.capture.name.startswith("captures/payments/"))
        self.assertTrue(
            payment.capture.name.endswith(".jpg")
            or payment.capture.name.endswith(".jpeg")
        )

    def test_payment_without_capture(self):
        payment_data = self.payment_data.copy()
        payment_data.pop("capture")

        with self.assertRaises(ValidationError):
            payment = Payment(**payment_data)
            payment.full_clean()

    def test_payment_invalid_capture_type(self):
        self.payment_data["capture"] = SimpleUploadedFile(
            "test_doc.txt", b"file_content", content_type="text/plain"
        )

        with self.assertRaises(ValidationError):
            payment = Payment(**self.payment_data)
            payment.full_clean()

    def test_payment_date_validation(self):
        # Fecha pasada debería ser válida
        self.payment_data["payment_date"] = "2023-01-01"
        payment = PaymentFactory.build(**self.payment_data)
        try:
            payment.full_clean()
        except ValidationError:
            self.fail("No debería fallar con fecha pasada")

    def test_date_auto_now(self):
        payment = PaymentFactory(**self.payment_data)
        self.assertIsNotNone(payment.date)
        self.assertTrue(isinstance(payment.date, datetime))

    def test_unique_reference(self):
        payment1 = PaymentFactory(**self.payment_data)
        payment2_data = self.payment_data.copy()
        payment2_data["reference"] = payment1.reference

        with self.assertRaises(ValidationError):
            payment2 = PaymentFactory.build(**payment2_data)
            payment2.full_clean()

    def test_reference_max_length(self):
        self.payment_data["reference"] = "1" * 21

        with self.assertRaises(ValidationError):
            payment = PaymentFactory.build(**self.payment_data)
            payment.full_clean()


class MobilePaymentModelTest(TestCase):
    def setUp(self):
        self.user = UserFactory(email="testuser", password="12345")
        self.mobile_payment_data = {
            "status": "pending",
            "bank": "0134",
            "dealer": self.user,
            "amount": 100.50,
            "id_number": "12345678",
            "payment_date": "2024-07-05",
            "reference": "REF123456789",
            "capture": SimpleUploadedFile(
                "test_image.jpg", b"file_content", content_type="image/jpeg"
            ),
            "phone_code": "0412",
            "phone_number": "1234567",
        }

    def tearDown(self):
        """Limpia los archivos de prueba después de cada test"""
        for payment in Payment.objects.all():
            if payment.capture and os.path.exists(payment.capture.path):
                try:
                    os.remove(payment.capture.path)
                except FileNotFoundError:
                    pass

    def test_mobile_payment_creation(self):
        mobile_payment = MobilePaymentFactory(**self.mobile_payment_data)
        self.assertTrue(isinstance(mobile_payment, MobilePayment))
        self.assertEqual(mobile_payment.payment_type, "mobile")

    def test_phone_code_choices(self):
        mobile_payment = MobilePaymentFactory(**self.mobile_payment_data)
        self.assertIn(mobile_payment.phone_code, dict(MobilePayment.PHONE_CODES))

    def test_invalid_phone_number_too_short(self):
        self.mobile_payment_data["phone_number"] = "123456"
        with self.assertRaises(ValidationError):
            mobile_payment = MobilePaymentFactory.build(**self.mobile_payment_data)
            mobile_payment.full_clean()

    def test_invalid_phone_number_too_long(self):
        self.mobile_payment_data["phone_number"] = "123456789"
        with self.assertRaises(ValidationError):
            mobile_payment = MobilePaymentFactory.build(**self.mobile_payment_data)
            mobile_payment.full_clean()

    def test_invalid_phone_number_not_numeric(self):
        self.mobile_payment_data["phone_number"] = "abcdefg"
        with self.assertRaises(ValidationError):
            mobile_payment = MobilePaymentFactory.build(**self.mobile_payment_data)
            mobile_payment.full_clean()

    def test_valid_phone_number(self):
        valid_phone_numbers = ["1234567", "9876543"]
        for phone_number in valid_phone_numbers:
            self.mobile_payment_data["phone_number"] = phone_number
            mobile_payment = MobilePaymentFactory.build(**self.mobile_payment_data)
            try:
                mobile_payment.full_clean()
            except ValidationError:
                self.fail(
                    f"ValidationError raised with valid phone_number: {phone_number}"
                )

    def test_payment_type_auto_set(self):
        mobile_payment = MobilePaymentFactory(**self.mobile_payment_data)

        self.assertEqual(mobile_payment.payment_type, "mobile")

        mobile_payment.payment_type = "bank"
        mobile_payment.save()
        mobile_payment.refresh_from_db()

        self.assertEqual(mobile_payment.payment_type, "mobile")


class DealerBalanceTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.past_promotion = PromotionFactory(past=True)
        cls.current_promotion = PromotionFactory()
        cls.user = UserFactory()
        cls.dealer = DealerFactory(user=cls.user, email=cls.user.email)
        cls.past_edition = EditionFactory(promotion=cls.past_promotion)
        cls.current_edition = EditionFactory(
            promotion=cls.current_promotion, collection__name="Angela", circulation=2
        )
        OrderFactory(
            date=cls.past_promotion.start_date,
            dealer=cls.dealer.user,
            edition=cls.past_edition,
        )
        OrderFactory(
            date=cls.current_promotion.start_date,
            dealer=cls.dealer.user,
            edition=cls.current_edition,
        )

    def setUp(self):
        self.past_dealer_balance = DealerBalanceFactory(
            start_date=self.past_promotion.start_date,
            dealer=self.dealer.user,
            promotion=self.past_promotion,
            initial_balance=Decimal("100.00"),
        )

        self.current_dealer_balance = DealerBalanceFactory(
            dealer=self.dealer.user,
            promotion=self.current_promotion,
            start_date=self.past_promotion.end_date + timedelta(days=1),
            initial_balance=self.past_dealer_balance.current_balance,
        )

    def tearDown(self):
        """Limpia los archivos de prueba después de cada test"""
        for payment in Payment.objects.all():
            if payment.capture and os.path.exists(payment.capture.path):
                try:
                    os.remove(payment.capture.path)
                except FileNotFoundError:
                    pass

    def test_dealer_balance_data(self):

        self.assertEqual(DealerBalance.objects.count(), 2)
        self.assertEqual(self.past_dealer_balance.dealer, self.dealer.user)
        self.assertEqual(self.current_dealer_balance.dealer, self.dealer.user)
        self.assertEqual(self.past_dealer_balance.promotion, self.past_promotion)
        self.assertEqual(self.current_dealer_balance.promotion, self.current_promotion)
        self.assertEqual(self.past_dealer_balance.initial_balance, 100)
        self.assertEqual(self.current_dealer_balance.initial_balance, 122.50)
        self.assertEqual(
            self.past_dealer_balance.start_date, self.past_promotion.start_date
        )
        self.assertEqual(
            self.current_dealer_balance.start_date,
            self.past_promotion.end_date + timedelta(days=1),
        )
        self.assertEqual(
            self.past_dealer_balance.end_date, self.past_promotion.end_date
        )
        self.assertEqual(
            self.current_dealer_balance.end_date,
            self.current_promotion.end_date,
        )
        self.assertEqual(self.past_dealer_balance.orders_total, 22.50)
        self.assertEqual(self.current_dealer_balance.orders_total, 45)
        self.assertEqual(self.past_dealer_balance.payments_total, 0)
        self.assertEqual(self.current_dealer_balance.payments_total, 0)
        self.assertEqual(self.past_dealer_balance.current_balance, 122.50)
        self.assertEqual(self.current_dealer_balance.current_balance, 167.50)

    def test_balance_data_after_add_payment_to_past_balance(self):

        payment = PaymentFactory(
            dealer=self.dealer.user,
            payment_date=self.past_promotion.start_date,
            amount="25",
        )
        payment.status = "completed"
        payment.save()
        payment.refresh_from_db()

        self.assertEqual(self.past_dealer_balance.orders_total, 22.50)
        self.assertEqual(self.past_dealer_balance.payments_total, 25)
        self.assertEqual(self.current_dealer_balance.orders_total, 45)
        self.assertEqual(self.current_dealer_balance.payments_total, 0)
        self.assertEqual(self.past_dealer_balance.current_balance, 97.50)
        self.current_dealer_balance.refresh_from_db()

        self.assertEqual(self.current_dealer_balance.initial_balance, 97.50)
        self.assertEqual(self.current_dealer_balance.current_balance, 142.50)

    def test_balance_data_after_add_payment_to_current_balance(self):
        payment = PaymentFactory(
            dealer=self.dealer.user,
            payment_date=self.current_promotion.start_date,
            amount="25",
        )
        payment.status = "completed"
        payment.save()
        self.current_dealer_balance.refresh_from_db()
        self.assertEqual(self.past_dealer_balance.orders_total, 22.50)
        self.assertEqual(self.past_dealer_balance.payments_total, 0)
        self.assertEqual(self.current_dealer_balance.orders_total, 45)
        self.assertEqual(self.current_dealer_balance.payments_total, 25)
        self.assertEqual(self.past_dealer_balance.current_balance, 122.50)
        self.assertEqual(self.current_dealer_balance.initial_balance, 122.50)
        self.assertEqual(self.current_dealer_balance.current_balance, 142.50)

    def test_balance_data_after_add_payments_out_of_promotions_ranges(self):
        payment = PaymentFactory(
            dealer=self.dealer.user,
            payment_date=self.past_promotion.start_date - timedelta(days=1),
            amount="25",
        )
        payment.status = "completed"
        payment.save()

        payment2 = PaymentFactory(
            dealer=self.dealer.user,
            payment_date=self.past_promotion.end_date + timedelta(days=1),
            amount="15",
        )
        payment2.status = "completed"
        payment2.save()

        payment3 = PaymentFactory(
            dealer=self.dealer.user,
            payment_date=self.current_promotion.end_date + timedelta(days=1),
            amount="50",
        )
        payment3.status = "completed"
        payment3.save()

        self.current_dealer_balance.refresh_from_db()
        self.assertEqual(Payment.objects.count(), 3)
        self.assertEqual(self.past_dealer_balance.orders_total, 22.50)
        self.assertEqual(self.current_dealer_balance.orders_total, 45)
        self.assertEqual(self.past_dealer_balance.payments_total, 0)
        self.assertEqual(self.current_dealer_balance.payments_total, 15.00)
        self.assertEqual(self.past_dealer_balance.current_balance, 122.50)
        self.assertEqual(self.current_dealer_balance.initial_balance, 122.50)
        self.assertEqual(self.current_dealer_balance.current_balance, 152.50)

    def test_balance_data_after_add_no_completed_payments(self):
        PaymentFactory(
            dealer=self.dealer.user,
            payment_date=self.past_promotion.start_date,
            amount="25",
        )
        PaymentFactory(
            dealer=self.dealer.user,
            payment_date=self.past_promotion.end_date + timedelta(days=1),
            amount="15",
        )
        PaymentFactory(
            dealer=self.dealer.user,
            payment_date=self.current_promotion.end_date,
            amount="50",
        )
        self.current_dealer_balance.refresh_from_db()
        self.assertEqual(Payment.objects.count(), 3)
        self.assertEqual(self.past_dealer_balance.orders_total, 22.50)
        self.assertEqual(self.current_dealer_balance.orders_total, 45)
        self.assertEqual(self.past_dealer_balance.payments_total, 0)
        self.assertEqual(self.current_dealer_balance.payments_total, 0)
        self.assertEqual(self.past_dealer_balance.current_balance, 122.50)
        self.assertEqual(self.current_dealer_balance.initial_balance, 122.50)
        self.assertEqual(self.current_dealer_balance.current_balance, 167.50)

    def test_negative_balance(self):
        payment = PaymentFactory(
            dealer=self.dealer.user,
            payment_date=self.past_promotion.start_date,
            amount="200",
        )
        payment.status = "completed"
        payment.save()

        self.past_dealer_balance.refresh_from_db()
        self.assertEqual(self.past_dealer_balance.current_balance, -77.50)

    def test_balance_data_after_change_payment_status(self):
        payment = PaymentFactory(
            dealer=self.dealer.user,
            payment_date=self.past_promotion.start_date,
            amount="25",
        )
        payment.status = "completed"
        payment.save()

        payment_2 = PaymentFactory(
            dealer=self.dealer.user,
            payment_date=self.current_promotion.start_date,
            amount="25",
        )
        payment_2.status = "completed"
        payment_2.save()

        self.past_dealer_balance.refresh_from_db()
        self.current_dealer_balance.refresh_from_db()

        self.assertEqual(self.past_dealer_balance.orders_total, 22.50)
        self.assertEqual(self.past_dealer_balance.payments_total, 25)
        self.assertEqual(self.current_dealer_balance.orders_total, 45)
        self.assertEqual(self.current_dealer_balance.payments_total, 25)
        self.assertEqual(self.past_dealer_balance.current_balance, 97.50)
        self.assertEqual(self.current_dealer_balance.initial_balance, 97.50)
        self.assertEqual(self.current_dealer_balance.current_balance, 117.50)

        payment.status = "rejected"
        payment.save()
        payment_2.status = "pending"
        payment_2.save()

        self.past_dealer_balance.refresh_from_db()
        self.current_dealer_balance.refresh_from_db()

        self.assertEqual(self.past_dealer_balance.orders_total, 22.50)
        self.assertEqual(self.past_dealer_balance.payments_total, 0)
        self.assertEqual(self.current_dealer_balance.orders_total, 45)
        self.assertEqual(self.current_dealer_balance.payments_total, 0)
        self.assertEqual(self.past_dealer_balance.current_balance, 122.50)
        self.assertEqual(self.current_dealer_balance.initial_balance, 122.50)
        self.assertEqual(self.current_dealer_balance.current_balance, 167.50)

    def test_balance_data_after_delete_payments(self):
        payment = PaymentFactory(
            dealer=self.dealer.user,
            payment_date=self.past_promotion.start_date,
            amount="25",
        )
        payment.status = "completed"
        payment.save()

        payment_2 = PaymentFactory(
            dealer=self.dealer.user,
            payment_date=self.current_promotion.start_date,
            amount="25",
        )
        payment_2.status = "completed"
        payment_2.save()

        self.past_dealer_balance.refresh_from_db()
        self.current_dealer_balance.refresh_from_db()

        self.assertEqual(self.past_dealer_balance.orders_total, 22.50)
        self.assertEqual(self.past_dealer_balance.payments_total, 25)
        self.assertEqual(self.current_dealer_balance.orders_total, 45)
        self.assertEqual(self.current_dealer_balance.payments_total, 25)
        self.assertEqual(self.past_dealer_balance.current_balance, 97.50)
        self.assertEqual(self.current_dealer_balance.initial_balance, 97.50)
        self.assertEqual(self.current_dealer_balance.current_balance, 117.50)
        payment.capture.delete(save=False)
        payment.delete()
        payment_2.capture.delete(save=False)
        payment_2.delete()

        self.past_dealer_balance.refresh_from_db()
        self.current_dealer_balance.refresh_from_db()

        self.assertEqual(self.past_dealer_balance.orders_total, 22.50)
        self.assertEqual(self.past_dealer_balance.payments_total, 0)
        self.assertEqual(self.current_dealer_balance.orders_total, 45)
        self.assertEqual(self.current_dealer_balance.payments_total, 0)
        self.assertEqual(self.past_dealer_balance.current_balance, 122.50)
        self.assertEqual(self.current_dealer_balance.initial_balance, 122.50)
        self.assertEqual(self.current_dealer_balance.current_balance, 167.50)
