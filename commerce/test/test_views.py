import io, os
from PIL import Image
from datetime import timedelta
from decimal import Decimal
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase
from promotions.models import Promotion
from promotions.test.factories import PromotionFactory
from editions.test.factories import EditionFactory
from authentication.test.factories import UserFactory
from users.test.factories import DealerFactory
from commerce.models import Order, Sale
from users.test.factories import CollectorFactory
from promotions.tasks import check_ended_promotions
from .factories import OrderFactory, PaymentFactory
from rest_framework import status
from ..serializers import OrderSerializer, PaymentSerializer
from ..models import Payment, MobilePayment
from commerce.models import DealerBalance
from commerce.test.factories import DealerBalanceFactory


class OrderListCreateAPIViewAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.promotion = PromotionFactory()
        cls.edition = EditionFactory(promotion=cls.promotion)
        cls.edition_2 = EditionFactory(
            promotion=cls.promotion, collection__name="Angela"
        )
        cls.superuser = UserFactory(is_superuser=True)
        cls.user_dealer = UserFactory()
        cls.dealer = DealerFactory(user=cls.user_dealer)
        cls.basic_user = UserFactory()
        cls.url = reverse("order-list-create")

    def tearDown(self):
        Order.objects.all().delete()

    def test_dealer_can_get_order_list(self):
        OrderFactory(dealer=self.dealer.user, edition=self.edition)
        OrderFactory(dealer=self.dealer.user, edition=self.edition_2)

        self.client.force_authenticate(user=self.dealer.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        for order in response.data:
            self.assertEqual(
                order, OrderSerializer(Order.objects.get(pk=order["id"])).data
            )

    def test_superuser_cannot_get_order_list(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"], "Solo los detallistas pueden realizar esta acción"
        )

    def test_basic_user_cannot_get_order_list(self):
        self.client.force_authenticate(user=self.basic_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"], "Solo los detallistas pueden realizar esta acción"
        )

    def test_unauthorized_user_cannot_get_order_list(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Debe iniciar sesión para realizar esta acción"
        )

    def test_dealer_can_create_order(self):
        self.client.force_authenticate(user=self.dealer.user)
        data = {"edition": self.edition.id}

        response = self.client.post(self.url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data,
            OrderSerializer(Order.objects.get(pk=response.data["id"])).data,
        )

    def test_superuser_cannot_create_order(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"], "Solo los detallistas pueden realizar esta acción"
        )

    def test_basic_user_cannot_create_order(self):
        self.client.force_authenticate(user=self.basic_user)
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"], "Solo los detallistas pueden realizar esta acción"
        )

    def test_unauthorized_user_cannot_create_order(self):
        self.client.logout()
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Debe iniciar sesión para realizar esta acción"
        )

    def test_create_order_without_active_promotion(self):
        Promotion.objects.all().delete()
        promotion = PromotionFactory(past=True)
        edition = EditionFactory(promotion=promotion, collection__name="freefire")
        self.client.force_authenticate(user=self.dealer.user)
        data = {"edition": edition.id}

        response = self.client.post(self.url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"],
            "No hay ninguna promoción en curso; no se puede realizar esta acción",
        )

    def test_create_order_without_edition_id(self):
        self.client.force_authenticate(user=self.dealer.user)
        data = {}

        response = self.client.post(self.url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"], "El campo edition no puede estar vacío"
        )

    def test_create_order_with_invalid_edition_id(self):
        self.client.force_authenticate(user=self.dealer.user)
        data = {"edition": 10000}

        response = self.client.post(self.url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"], "No existe ninguna edición con el id suministrado"
        )

    def test_create_order_with_no_available_box(self):
        dealer = DealerFactory(user=UserFactory())
        OrderFactory(edition=self.edition, dealer=dealer.user)
        self.client.force_authenticate(user=self.dealer.user)
        data = {"edition": self.edition.id}

        response = self.client.post(self.url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"], "No hay paquetes disponibles para esta edición"
        )

    def test_create_order_with_invalid_data_format(self):
        self.client.force_authenticate(user=self.dealer.user)
        data = "invalid_json_data"  # Esto provocará un error de parsing

        response = self.client.post(self.url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_amount_calculation(self):
        self.promotion.pack_cost = Decimal("2.50")
        self.promotion.save()
        box = self.edition.boxes.all().first()
        packs = box.packs.all().count()
        amount = self.promotion.pack_cost * packs

        self.client.force_authenticate(user=self.dealer.user)
        data = {"edition": self.edition.id}

        response = self.client.post(self.url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["amount"], str(amount))

    def test_method_not_allowed(self):
        self.client.force_authenticate(user=self.dealer.user)
        data = {"edition": self.edition.id}

        response = self.client.put(self.url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data["detail"], 'Método "PUT" no permitido.')


class PaymentListAPIViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.promotion = PromotionFactory()
        cls.superuser = UserFactory(is_superuser=True)
        cls.basic_user = UserFactory()
        cls.dealer_user = UserFactory()
        cls.dealer_user_2 = UserFactory()
        cls.dealer = DealerFactory(user=cls.dealer_user)
        cls.dealer_2 = DealerFactory(user=cls.dealer_user_2)
        cls.url = reverse("payment-list")

    def setUp(self):
        self.client.force_authenticate(user=self.dealer.user)
        self.payment = PaymentFactory(dealer=self.dealer.user)
        self.payment_2 = PaymentFactory(dealer=self.dealer.user)
        self.payment_3 = PaymentFactory(dealer=self.dealer_2.user)

    def tearDown(self):
        """Limpia los archivos de prueba después de cada test"""
        for payment in Payment.objects.all():
            if payment.capture and os.path.exists(payment.capture.path):
                try:
                    os.remove(payment.capture.path)
                except FileNotFoundError:
                    pass

    def test_dealer_can_get_payments_list(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Payment.objects.count(), 3)
        self.assertEqual(len(response.data), 2)

        for payment in response.data:
            bd_payment = Payment.objects.get(pk=payment["id"])
            serializer = PaymentSerializer(bd_payment).data

            for key, value in payment.items():
                if key != "capture":
                    self.assertEqual(value, serializer[key])
                self.assertTrue(payment["capture"].endswith(serializer["capture"]))

    def test_dealer_2_can_get_payments_list(self):
        self.client.logout()
        self.client.force_authenticate(user=self.dealer_2.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Payment.objects.count(), 3)
        self.assertEqual(len(response.data), 1)

        for payment in response.data:
            bd_payment = Payment.objects.get(pk=payment["id"])
            serializer = PaymentSerializer(bd_payment).data

            for key, value in payment.items():
                if key != "capture":
                    self.assertEqual(value, serializer[key])
                self.assertTrue(payment["capture"].endswith(serializer["capture"]))

    def test_superuser_cannot_get_payments_list(self):
        self.client.logout()
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"], "Solo los detallistas pueden realizar esta acción"
        )

    def test_basic_user_cannot_get_payments_list(self):
        self.client.logout()
        self.client.force_authenticate(user=self.basic_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"], "Solo los detallistas pueden realizar esta acción"
        )

    def test_unauthenticated_user_cannot_get_payments_list(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Debe iniciar sesión para realizar esta acción"
        )

    def test_payment_list_view_without_active_promotion(self):
        self.promotion.delete()
        PromotionFactory(past=True)
        self.client.force_authenticate(user=self.dealer.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_payment_list_view_with_active_promotion_no_payments(self):
        self.tearDown()
        Payment.objects.all().delete()
        self.client.force_authenticate(user=self.dealer.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(
            response.data["detail"],
            "No hay pagos registrados.",
        )

    def test_method_not_allowed(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(str(response.data["detail"]), 'Método "POST" no permitido.')


class PaymentCreateViewAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.promotion = PromotionFactory()
        cls.superuser = UserFactory(is_superuser=True)
        cls.basic_user = UserFactory()
        cls.dealer_user = UserFactory()
        cls.dealer = DealerFactory(user=cls.dealer_user, email=cls.dealer_user.email)
        cls.url = reverse("payment-create")
        image = Image.new("RGB", (100, 100))
        image_io = io.BytesIO()
        image.save(image_io, format="JPEG")
        cls.image_file = SimpleUploadedFile(
            "test_image.jpg", image_io.getvalue(), content_type="image/jpeg"
        )
        cls.sale_data = {
            "payment_date": timezone.now().date(),
            "bank": "0108",
            "amount": Decimal("125.50"),
            "reference": "1234567890",
            "id_number": "12345678",
            "capture": cls.image_file,
        }

    def setUp(self):
        self.client.force_authenticate(user=self.dealer.user)

    def tearDown(self):
        """Limpia los archivos de prueba después de cada test"""
        for payment in Payment.objects.all():
            if payment.capture and os.path.exists(payment.capture.path):
                try:
                    os.remove(payment.capture.path)
                except FileNotFoundError:
                    pass

    def test_dealer_can_create_payment(self):
        response = self.client.post(self.url, self.sale_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(response.data["id"], 1)
        self.assertEqual(response.data["status"], "pending")
        self.assertEqual(response.data["dealer"], self.dealer.user.id)
        self.assertEqual(response.data["dealer_email"], self.dealer.email)
        self.assertEqual(
            response.data["payment_date"], str(self.sale_data["payment_date"])
        )
        self.assertEqual(response.data["bank"], self.sale_data["bank"])
        self.assertEqual(response.data["bank_name"], "BBVA Provincial")
        self.assertEqual(Decimal(response.data["amount"]), self.sale_data["amount"])
        self.assertEqual(response.data["reference"], self.sale_data["reference"])
        self.assertEqual(response.data["id_number"], self.sale_data["id_number"])
        self.assertTrue(
            response.data["capture"].endswith(
                PaymentSerializer(Payment.objects.get(pk=response.data["id"])).data[
                    "capture"
                ]
            )
        )
        self.assertEqual(response.data["payment_type"], "bank")

    def test_superuser_cannot_create_payment(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.post(self.url, self.sale_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"], "Solo los detallistas pueden realizar esta acción"
        )

    def test_basic_user_cannot_create_payment(self):
        self.client.force_authenticate(user=self.basic_user)
        response = self.client.post(self.url, self.sale_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"], "Solo los detallistas pueden realizar esta acción"
        )

    def test_unauthenticated_user_cannot_create_payment(self):
        self.client.logout()
        response = self.client.post(self.url, self.sale_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Debe iniciar sesión para realizar esta acción"
        )

    def test_method_not_allowed(self):
        response = self.client.get(self.url, self.sale_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(str(response.data["detail"]), 'Método "GET" no permitido.')

    def test_payment_create_view_with_future_payment_date(self):
        invalid_data = self.sale_data.copy()
        invalid_data["payment_date"] = timezone.now().date() + timedelta(days=1)
        response = self.client.post(self.url, invalid_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["payment_date"][0]),
            "La fecha de pago no puede ser en el futuro.",
        )

    def test_payment_create_view_with_datetime_payment_date(self):
        invalid_data = self.sale_data.copy()
        invalid_data["payment_date"] = timezone.now() + timedelta(days=1)
        response = self.client.post(self.url, invalid_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["payment_date"][0]),
            "Fecha con formato erróneo. Use uno de los siguientes formatos en su lugar: YYYY-MM-DD.",
        )

    def test_payment_create_view_with_invalid_payment_date_format(self):
        invalid_data = self.sale_data.copy()
        invalid_data["payment_date"] = "invalid"
        response = self.client.post(self.url, invalid_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["payment_date"][0]),
            "Fecha con formato erróneo. Use uno de los siguientes formatos en su lugar: YYYY-MM-DD.",
        )

    def test_payment_create_view_with_no_payment_date(self):
        invalid_data = self.sale_data.copy()
        invalid_data.pop("payment_date")
        response = self.client.post(self.url, invalid_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["payment_date"][0]),
            "Este campo es requerido.",
        )

    def test_payment_create_view_with_no_numeric_amount(self):
        invalid_data = self.sale_data.copy()
        invalid_data["amount"] = "invalid"
        response = self.client.post(self.url, invalid_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["amount"][0]), "Se requiere un número válido."
        )

    def test_payment_create_view_with_negative_amount(self):
        invalid_data = self.sale_data.copy()
        invalid_data["amount"] = Decimal("-125.50")
        response = self.client.post(self.url, invalid_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["amount"][0]), "El monto debe ser mayor que cero."
        )

    def test_payment_create_view_with_no_amount(self):
        invalid_data = self.sale_data.copy()
        invalid_data.pop("amount")
        response = self.client.post(self.url, invalid_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["amount"][0]),
            "Este campo es requerido.",
        )

    def test_payment_create_view_with_big_amount(self):
        data = self.sale_data.copy()
        data["amount"] = Decimal("99999999.99")
        response = self.client.post(self.url, data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_payment_create_view_with_too_big_amount(self):
        data = self.sale_data.copy()
        data["amount"] = Decimal("999999991.99")
        response = self.client.post(self.url, data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["amount"][0]),
            "Asegúrese de que no haya más de 10 dígitos en total.",
        )

    def test_payment_create_view_with_no_reference(self):
        invalid_data = self.sale_data.copy()
        invalid_data.pop("reference")
        response = self.client.post(self.url, invalid_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["reference"][0]),
            "Este campo es requerido.",
        )

    def test_payment_create_view_too_long_reference(self):
        data = self.sale_data.copy()
        data["reference"] = "refg34567987654323765"
        response = self.client.post(self.url, data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["reference"][0]),
            "Asegúrese de que este campo no tenga más de 20 caracteres.",
        )

    def test_payment_create_with_duplicated_reference(self):
        PaymentFactory(reference="1234567890", dealer=self.dealer.user)
        data = self.sale_data.copy()
        data["reference"] = "1234567890"
        response = self.client.post(self.url, data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["reference"][0]),
            "La referencia del pago ya existe",
        )

    def test_payment_create_view_with_invalid_status(self):
        invalid_data = self.sale_data.copy()
        invalid_data["status"] = "invalid"
        response = self.client.post(self.url, invalid_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["status"][0]),
            '"invalid" no es una elección válida.',
        )

    def test_payment_create_view_with_no_bank(self):
        invalid_data = self.sale_data.copy()
        invalid_data.pop("bank")
        response = self.client.post(self.url, invalid_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["bank"][0]),
            "Este campo es requerido.",
        )

    def test_payment_create_view_with_invalid_bank(self):
        data = self.sale_data.copy()
        data["bank"] = "10343"
        response = self.client.post(self.url, data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["bank"][0]),
            '"10343" no es una elección válida.',
        )

    def test_payment_create_view_with_no_id_number(self):
        invalid_data = self.sale_data.copy()
        invalid_data.pop("id_number")
        response = self.client.post(self.url, invalid_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["id_number"][0]),
            "Este campo es requerido.",
        )

    def test_payment_create_view_with_no_numeric_id_number(self):
        invalid_data = self.sale_data.copy()
        invalid_data["id_number"] = "invalid"
        response = self.client.post(self.url, invalid_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["id_number"][0]),
            "Ingrese un número de cédula válido (6 hasta 8 dígitos)",
        )

    def test_payment_create_view_with_too_short_id_number(self):
        invalid_data = self.sale_data.copy()
        invalid_data["id_number"] = "12345"
        response = self.client.post(self.url, invalid_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["id_number"][0]),
            "Ingrese un número de cédula válido (6 hasta 8 dígitos)",
        )

    def test_payment_create_view_with_too_long_id_number(self):
        invalid_data = self.sale_data.copy()
        invalid_data["id_number"] = "123456789"
        response = self.client.post(self.url, invalid_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["id_number"][0]),
            "Ingrese un número de cédula válido (6 hasta 8 dígitos)",
        )

    def test_payment_create_with_invalid_payment_type(self):
        data = self.sale_data.copy()
        data["payment_type"] = "invalid"
        response = self.client.post(self.url, data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["payment_type"][0]),
            '"invalid" no es una elección válida.',
        )

    def test_payment_type_setting(self):
        data = self.sale_data.copy()
        data["payment_type"] = "mobile"
        response = self.client.post(self.url, data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data["payment_type"],
            "bank",
        )


class MobilePaymentCreateViewAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.promotion = PromotionFactory()
        cls.superuser = UserFactory(is_superuser=True)
        cls.basic_user = UserFactory()
        cls.dealer_user = UserFactory()
        cls.dealer = DealerFactory(user=cls.dealer_user, email=cls.dealer_user.email)
        cls.url = reverse("mobile-payment-create")
        image = Image.new("RGB", (100, 100))
        image_io = io.BytesIO()
        image.save(image_io, format="JPEG")
        cls.image_file = SimpleUploadedFile(
            "test_image.jpg", image_io.getvalue(), content_type="image/jpeg"
        )
        cls.mobile_sale_data = {
            "payment_date": timezone.now().date(),
            "bank": "0108",
            "amount": Decimal("125.50"),
            "reference": "1234567890",
            "id_number": "12345678",
            "capture": cls.image_file,
            "phone_code": "0416",
            "phone_number": "4994433",
            "payment_type": "mobile",
        }

    def setUp(self):
        self.client.force_authenticate(user=self.dealer.user)

    def tearDown(self):
        """Limpia los archivos de prueba después de cada test"""
        for payment in Payment.objects.all():
            if payment.capture and os.path.exists(payment.capture.path):
                try:
                    os.remove(payment.capture.path)
                except FileNotFoundError:
                    pass

    def test_dealer_can_create_mobile_payment(self):
        response = self.client.post(self.url, self.mobile_sale_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(MobilePayment.objects.count(), 1)
        self.assertEqual(response.data["id"], 1)
        self.assertEqual(response.data["status"], "pending")
        self.assertEqual(response.data["dealer"], self.dealer.user.id)
        self.assertEqual(response.data["dealer_email"], self.dealer.email)
        self.assertEqual(
            response.data["payment_date"], str(self.mobile_sale_data["payment_date"])
        )
        self.assertEqual(response.data["bank"], self.mobile_sale_data["bank"])
        self.assertEqual(response.data["bank_name"], "BBVA Provincial")
        self.assertEqual(
            Decimal(response.data["amount"]), self.mobile_sale_data["amount"]
        )
        self.assertEqual(response.data["reference"], self.mobile_sale_data["reference"])
        self.assertEqual(response.data["id_number"], self.mobile_sale_data["id_number"])
        self.assertEqual(
            response.data["payment_type"], self.mobile_sale_data["payment_type"]
        )
        self.assertTrue(
            response.data["capture"].endswith(
                PaymentSerializer(Payment.objects.get(pk=response.data["id"])).data[
                    "capture"
                ]
            )
        )

    def test_superuser_cannot_create_mobile_payment(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.post(self.url, self.mobile_sale_data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"], "Solo los detallistas pueden realizar esta acción"
        )

    def test_basic_user_cannot_create_mobile_payment(self):
        self.client.force_authenticate(user=self.basic_user)
        response = self.client.post(self.url, self.mobile_sale_data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"], "Solo los detallistas pueden realizar esta acción"
        )

    def test_unauthenticated_user_cannot_create_mobile_payment(self):
        self.client.logout()
        response = self.client.post(self.url, self.mobile_sale_data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Debe iniciar sesión para realizar esta acción"
        )

    def test_mobile_payment_create_view_with_no_phone_code(self):
        invalid_data = self.mobile_sale_data.copy()
        invalid_data.pop("phone_code")
        response = self.client.post(self.url, invalid_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["phone_code"][0]),
            "Este campo es requerido.",
        )

    def test_payment_create_view_with_invalid_phone_code(self):
        invalid_data = self.mobile_sale_data.copy()
        invalid_data["phone_code"] = "invalid"
        response = self.client.post(self.url, invalid_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["phone_code"][0]),
            '"invalid" no es una elección válida.',
        )

    def test_mobile_payment_create_view_with_no_phone_number(self):
        invalid_data = self.mobile_sale_data.copy()
        invalid_data.pop("phone_number")
        response = self.client.post(self.url, invalid_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["phone_number"][0]),
            "Este campo es requerido.",
        )

    def test_payment_create_view_with_no_numeric_phone_number(self):
        invalid_data = self.mobile_sale_data.copy()
        invalid_data["phone_number"] = "invalid"
        response = self.client.post(self.url, invalid_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["phone_number"][0]),
            "Ingrese un número de teléfono válido (7 dígitos)",
        )

    def test_payment_create_view_with_too_short_phone_number(self):
        invalid_data = self.mobile_sale_data.copy()
        invalid_data["phone_number"] = "123456"
        response = self.client.post(self.url, invalid_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["phone_number"][0]),
            "Ingrese un número de teléfono válido (7 dígitos)",
        )

    def test_payment_create_view_with_too_long_phone_number(self):
        invalid_data = self.mobile_sale_data.copy()
        invalid_data["phone_number"] = "12345678"
        response = self.client.post(self.url, invalid_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["phone_number"][0]),
            "Ingrese un número de teléfono válido (7 dígitos)",
        )

    def test_payment_create_view_with_incorrect_payment_type(self):
        invalid_data = self.mobile_sale_data.copy()
        invalid_data["payment_type"] = "bank"
        response = self.client.post(self.url, invalid_data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["non_field_errors"][0]),
            "El tipo de pago debe ser 'mobile' para pagos móviles.",
        )

    def test_method_not_allowed(self):
        response = self.client.get(self.url, self.mobile_sale_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(str(response.data["detail"]), 'Método "GET" no permitido.')


class PaymentOptionsViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.url = reverse("payment-options")
        cls.superuser = UserFactory(is_superuser=True)
        cls.basic_user = UserFactory()
        cls.dealer_user = UserFactory()
        cls.dealer = DealerFactory(user=cls.dealer_user)

    def test_dealer_can_get_payment_options(self):
        self.client.force_authenticate(user=self.dealer.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("banks", response.data)
        self.assertIn("payment_status", response.data)

        self.assertEqual(response.data["banks"], dict(Payment.BANKS))
        self.assertEqual(response.data["payment_status"], dict(Payment.PAYMENT_STATUS))

    def test_superuser_cannot_get_payment_options(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"], "Solo los detallistas pueden realizar esta acción"
        )

    def test_basic_user_cannot_get_payment_options(self):
        self.client.force_authenticate(user=self.basic_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"], "Solo los detallistas pueden realizar esta acción"
        )

    def test_unauthenticated_user_cannot_get_payment_options(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Debe iniciar sesión para realizar esta acción"
        )

    def test_post_not_allowed(self):
        self.client.force_authenticate(user=self.dealer.user)
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class MobilePaymentOptionsViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.url = reverse("mobile-payment-options")
        cls.superuser = UserFactory(is_superuser=True)
        cls.basic_user = UserFactory()
        cls.dealer_user = UserFactory()
        cls.dealer = DealerFactory(user=cls.dealer_user)

    def test_dealer_can_get__mobile_payment_options(self):
        self.client.force_authenticate(user=self.dealer.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("phone_codes", response.data)
        self.assertEqual(response.data["phone_codes"], dict(MobilePayment.PHONE_CODES))

    def test_superuser_cannot_get__mobile_payment_options(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"], "Solo los detallistas pueden realizar esta acción"
        )

    def test_basic_user_cannot_get__mobile_payment_options(self):
        self.client.force_authenticate(user=self.basic_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"], "Solo los detallistas pueden realizar esta acción"
        )

    def test_unauthenticated_user_cannot_get__mobile_payment_options(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Debe iniciar sesión para realizar esta acción"
        )

    def test_post_not_allowed(self):
        self.client.force_authenticate(user=self.dealer.user)
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class DealerBalanceViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.past_promotion = PromotionFactory(past=True)
        cls.superuser = UserFactory(is_superuser=True)
        cls.basic_user = UserFactory()
        cls.dealer = DealerFactory(email="dealer@test.com")
        # Se crea el primer balance con sin promocion
        cls.dealer_user = UserFactory(email=cls.dealer.email)
        check_ended_promotions()
        # se agrega la promotion al balance
        cls.promotion = PromotionFactory()
        cls.dealer.refresh_from_db()
        cls.url = reverse("dealer-balance")

    def setUp(self):
        self.client.force_authenticate(user=self.dealer.user)

    def test_get_last_dealer_balance(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(DealerBalance.objects.count(), 1)
        self.assertEqual(response.data["dealer"], self.dealer.user.id)
        self.assertEqual(response.data["promotion"], self.promotion.id)
        self.assertEqual(response.data["initial_balance"], "0.00")
        self.assertEqual(response.data["initial_balance"], "0.00")

    def test_superuser_cannot_get_last_dealer_balance(self):
        self.client.logout()
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"], "Solo los detallistas pueden realizar esta acción"
        )

    def test_basic_user_cannot_get_last_dealer_balance(self):
        self.client.logout()
        self.client.force_authenticate(user=self.basic_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"], "Solo los detallistas pueden realizar esta acción"
        )

    def test_unauthenticated_user_cannot_get_last_dealer_balance(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Debe iniciar sesión para realizar esta acción"
        )

    def test_method_not_allowed(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data["detail"], 'Método "POST" no permitido.')

    def test_no_balance_found(self):
        DealerBalance.objects.all().delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data["detail"],
            "No se encontró ningún balance para el usuario actual.",
        )


class SaleCreateViewAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.promotion = PromotionFactory()
        cls.edition = EditionFactory(promotion=PromotionFactory())
        cls.superuser = UserFactory(is_superuser=True)
        cls.basic_user = UserFactory()
        cls.dealer_user = UserFactory()
        cls.dealer = DealerFactory(user=cls.dealer_user, email=cls.dealer_user.email)
        cls.collector = CollectorFactory(user=UserFactory())
        cls.url = reverse("sale-create")
        cls.sale_data = {
            "edition": cls.edition.id,
            "dealer": cls.dealer_user.id,
            "collector": cls.collector.id,
            "quantity": 1,
        }

    def setUp(self):
        self.client.force_authenticate(user=self.dealer.user)

    def test_dealer_can_create_sale(self):
        response = self.client.post(self.url, self.sale_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Sale.objects.count(), 1)
        self.assertEqual(response.data["id"], 1)
        self.assertEqual(response.data["date"], timezone.now().date())
        self.assertEqual(response.data["edition"], self.edition.id)
        self.assertEqual(response.data["edition_name"], self.edition.name)
        self.assertEqual(response.data["dealer"], self.dealer.user.id)
        self.assertEqual(response.data["dealer_name"], self.dealer.get_fullname())
        self.assertEqual(response.data["collector"], self.collector.id)
        self.assertEqual(
            response.data["collector_name"], self.collector.get_full_name()
        )
        self.assertEqual(response.data["quantity"], 1)

    # def test_superuser_cannot_create_payment(self):
    #     self.client.force_authenticate(user=self.superuser)
    #     response = self.client.post(self.url, self.sale_data, format="multipart")

    #     self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    #     self.assertEqual(
    #         response.data["detail"], "Solo los detallistas pueden realizar esta acción"
    #     )

    # def test_basic_user_cannot_create_payment(self):
    #     self.client.force_authenticate(user=self.basic_user)
    #     response = self.client.post(self.url, self.sale_data, format="multipart")

    #     self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    #     self.assertEqual(
    #         response.data["detail"], "Solo los detallistas pueden realizar esta acción"
    #     )

    # def test_unauthenticated_user_cannot_create_payment(self):
    #     self.client.logout()
    #     response = self.client.post(self.url, self.sale_data, format="multipart")

    #     self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    #     self.assertEqual(
    #         response.data["detail"], "Debe iniciar sesión para realizar esta acción"
    #     )

    # def test_method_not_allowed(self):
    #     response = self.client.get(self.url, self.sale_data, format="multipart")

    #     self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    #     self.assertEqual(str(response.data["detail"]), 'Método "GET" no permitido.')

    # def test_payment_create_view_with_future_payment_date(self):
    #     invalid_data = self.sale_data.copy()
    #     invalid_data["payment_date"] = timezone.now().date() + timedelta(days=1)
    #     response = self.client.post(self.url, invalid_data, format="multipart")

    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertEqual(
    #         str(response.data["payment_date"][0]),
    #         "La fecha de pago no puede ser en el futuro.",
    #     )

    # def test_payment_create_view_with_datetime_payment_date(self):
    #     invalid_data = self.sale_data.copy()
    #     invalid_data["payment_date"] = timezone.now() + timedelta(days=1)
    #     response = self.client.post(self.url, invalid_data, format="multipart")

    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertEqual(
    #         str(response.data["payment_date"][0]),
    #         "Fecha con formato erróneo. Use uno de los siguientes formatos en su lugar: YYYY-MM-DD.",
    #     )

    # def test_payment_create_view_with_invalid_payment_date_format(self):
    #     invalid_data = self.sale_data.copy()
    #     invalid_data["payment_date"] = "invalid"
    #     response = self.client.post(self.url, invalid_data, format="multipart")

    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertEqual(
    #         str(response.data["payment_date"][0]),
    #         "Fecha con formato erróneo. Use uno de los siguientes formatos en su lugar: YYYY-MM-DD.",
    #     )

    # def test_payment_create_view_with_no_payment_date(self):
    #     invalid_data = self.sale_data.copy()
    #     invalid_data.pop("payment_date")
    #     response = self.client.post(self.url, invalid_data, format="multipart")

    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertEqual(
    #         str(response.data["payment_date"][0]),
    #         "Este campo es requerido.",
    #     )

    # def test_payment_create_view_with_no_numeric_amount(self):
    #     invalid_data = self.sale_data.copy()
    #     invalid_data["amount"] = "invalid"
    #     response = self.client.post(self.url, invalid_data, format="multipart")

    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertEqual(
    #         str(response.data["amount"][0]), "Se requiere un número válido."
    #     )

    # def test_payment_create_view_with_negative_amount(self):
    #     invalid_data = self.sale_data.copy()
    #     invalid_data["amount"] = Decimal("-125.50")
    #     response = self.client.post(self.url, invalid_data, format="multipart")

    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertEqual(
    #         str(response.data["amount"][0]), "El monto debe ser mayor que cero."
    #     )

    # def test_payment_create_view_with_no_amount(self):
    #     invalid_data = self.sale_data.copy()
    #     invalid_data.pop("amount")
    #     response = self.client.post(self.url, invalid_data, format="multipart")

    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertEqual(
    #         str(response.data["amount"][0]),
    #         "Este campo es requerido.",
    #     )

    # def test_payment_create_view_with_big_amount(self):
    #     data = self.sale_data.copy()
    #     data["amount"] = Decimal("99999999.99")
    #     response = self.client.post(self.url, data, format="multipart")

    #     self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # def test_payment_create_view_with_too_big_amount(self):
    #     data = self.sale_data.copy()
    #     data["amount"] = Decimal("999999991.99")
    #     response = self.client.post(self.url, data, format="multipart")

    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertEqual(
    #         str(response.data["amount"][0]),
    #         "Asegúrese de que no haya más de 10 dígitos en total.",
    #     )

    # def test_payment_create_view_with_no_reference(self):
    #     invalid_data = self.sale_data.copy()
    #     invalid_data.pop("reference")
    #     response = self.client.post(self.url, invalid_data, format="multipart")

    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertEqual(
    #         str(response.data["reference"][0]),
    #         "Este campo es requerido.",
    #     )

    # def test_payment_create_view_too_long_reference(self):
    #     data = self.sale_data.copy()
    #     data["reference"] = "refg34567987654323765"
    #     response = self.client.post(self.url, data, format="multipart")

    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertEqual(
    #         str(response.data["reference"][0]),
    #         "Asegúrese de que este campo no tenga más de 20 caracteres.",
    #     )

    # def test_payment_create_with_duplicated_reference(self):
    #     PaymentFactory(reference="1234567890", dealer=self.dealer.user)
    #     data = self.sale_data.copy()
    #     data["reference"] = "1234567890"
    #     response = self.client.post(self.url, data, format="multipart")

    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertEqual(
    #         str(response.data["reference"][0]),
    #         "La referencia del pago ya existe",
    #     )

    # def test_payment_create_view_with_invalid_status(self):
    #     invalid_data = self.sale_data.copy()
    #     invalid_data["status"] = "invalid"
    #     response = self.client.post(self.url, invalid_data, format="multipart")

    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertEqual(
    #         str(response.data["status"][0]),
    #         '"invalid" no es una elección válida.',
    #     )

    # def test_payment_create_view_with_no_bank(self):
    #     invalid_data = self.sale_data.copy()
    #     invalid_data.pop("bank")
    #     response = self.client.post(self.url, invalid_data, format="multipart")

    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertEqual(
    #         str(response.data["bank"][0]),
    #         "Este campo es requerido.",
    #     )

    # def test_payment_create_view_with_invalid_bank(self):
    #     data = self.sale_data.copy()
    #     data["bank"] = "10343"
    #     response = self.client.post(self.url, data, format="multipart")

    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertEqual(
    #         str(response.data["bank"][0]),
    #         '"10343" no es una elección válida.',
    #     )

    # def test_payment_create_view_with_no_id_number(self):
    #     invalid_data = self.sale_data.copy()
    #     invalid_data.pop("id_number")
    #     response = self.client.post(self.url, invalid_data, format="multipart")

    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertEqual(
    #         str(response.data["id_number"][0]),
    #         "Este campo es requerido.",
    #     )

    # def test_payment_create_view_with_no_numeric_id_number(self):
    #     invalid_data = self.sale_data.copy()
    #     invalid_data["id_number"] = "invalid"
    #     response = self.client.post(self.url, invalid_data, format="multipart")

    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertEqual(
    #         str(response.data["id_number"][0]),
    #         "Ingrese un número de cédula válido (6 hasta 8 dígitos)",
    #     )

    # def test_payment_create_view_with_too_short_id_number(self):
    #     invalid_data = self.sale_data.copy()
    #     invalid_data["id_number"] = "12345"
    #     response = self.client.post(self.url, invalid_data, format="multipart")

    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertEqual(
    #         str(response.data["id_number"][0]),
    #         "Ingrese un número de cédula válido (6 hasta 8 dígitos)",
    #     )

    # def test_payment_create_view_with_too_long_id_number(self):
    #     invalid_data = self.sale_data.copy()
    #     invalid_data["id_number"] = "123456789"
    #     response = self.client.post(self.url, invalid_data, format="multipart")

    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertEqual(
    #         str(response.data["id_number"][0]),
    #         "Ingrese un número de cédula válido (6 hasta 8 dígitos)",
    #     )

    # def test_payment_create_with_invalid_payment_type(self):
    #     data = self.sale_data.copy()
    #     data["payment_type"] = "invalid"
    #     response = self.client.post(self.url, data, format="multipart")

    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertEqual(
    #         str(response.data["payment_type"][0]),
    #         '"invalid" no es una elección válida.',
    #     )

    # def test_payment_type_setting(self):
    #     data = self.sale_data.copy()
    #     data["payment_type"] = "mobile"
    #     response = self.client.post(self.url, data, format="multipart")

    #     self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    #     self.assertEqual(
    #         response.data["payment_type"],
    #         "bank",
    #     )
