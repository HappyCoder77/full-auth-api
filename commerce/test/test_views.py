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
from commerce.models import Order
from .factories import Orderfactory, PaymentFactory
from rest_framework import status
from ..serializers import OrderSerializer, PaymentSerializer
from ..models import Payment, MobilePayment


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
        Orderfactory(dealer=self.dealer.user, edition=self.edition)
        Orderfactory(dealer=self.dealer.user, edition=self.edition_2)

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
        Orderfactory(edition=self.edition)
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
        cls.payment_data = {
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
        response = self.client.post(self.url, self.payment_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(response.data["id"], 1)
        self.assertEqual(response.data["status"], "pending")
        self.assertEqual(response.data["dealer"], self.dealer.user.id)
        self.assertEqual(response.data["dealer_email"], self.dealer.email)
        self.assertEqual(
            response.data["payment_date"], str(self.payment_data["payment_date"])
        )
        self.assertEqual(response.data["bank"], self.payment_data["bank"])
        self.assertEqual(response.data["bank_name"], "BBVA Provincial")
        self.assertEqual(Decimal(response.data["amount"]), self.payment_data["amount"])
        self.assertEqual(response.data["reference"], self.payment_data["reference"])
        self.assertEqual(response.data["id_number"], self.payment_data["id_number"])
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
        response = self.client.post(self.url, self.payment_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"], "Solo los detallistas pueden realizar esta acción"
        )

    def test_basic_user_cannot_create_payment(self):
        self.client.force_authenticate(user=self.basic_user)
        response = self.client.post(self.url, self.payment_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"], "Solo los detallistas pueden realizar esta acción"
        )

    def test_unauthenticated_user_cannot_create_payment(self):
        self.client.logout()
        response = self.client.post(self.url, self.payment_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Debe iniciar sesión para realizar esta acción"
        )

    def test_method_not_allowed(self):
        response = self.client.get(self.url, self.payment_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(str(response.data["detail"]), 'Método "GET" no permitido.')

    def test_payment_create_view_with_future_payment_date(self):
        invalid_data = self.payment_data.copy()
        invalid_data["payment_date"] = timezone.now().date() + timedelta(days=1)
        response = self.client.post(self.url, invalid_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["payment_date"][0]),
            "La fecha de pago no puede ser en el futuro.",
        )

    def test_payment_create_view_with_datetime_payment_date(self):
        invalid_data = self.payment_data.copy()
        invalid_data["payment_date"] = timezone.now() + timedelta(days=1)
        response = self.client.post(self.url, invalid_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["payment_date"][0]),
            "Fecha con formato erróneo. Use uno de los siguientes formatos en su lugar: YYYY-MM-DD.",
        )

    def test_payment_create_view_with_invalid_payment_date_format(self):
        invalid_data = self.payment_data.copy()
        invalid_data["payment_date"] = "invalid"
        response = self.client.post(self.url, invalid_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["payment_date"][0]),
            "Fecha con formato erróneo. Use uno de los siguientes formatos en su lugar: YYYY-MM-DD.",
        )

    def test_payment_create_view_with_no_payment_date(self):
        invalid_data = self.payment_data.copy()
        invalid_data.pop("payment_date")
        response = self.client.post(self.url, invalid_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["payment_date"][0]),
            "Este campo es requerido.",
        )

    def test_payment_create_view_with_no_numeric_amount(self):
        invalid_data = self.payment_data.copy()
        invalid_data["amount"] = "invalid"
        response = self.client.post(self.url, invalid_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["amount"][0]), "Se requiere un número válido."
        )

    def test_payment_create_view_with_negative_amount(self):
        invalid_data = self.payment_data.copy()
        invalid_data["amount"] = Decimal("-125.50")
        response = self.client.post(self.url, invalid_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["amount"][0]), "El monto debe ser mayor que cero."
        )

    def test_payment_create_view_with_no_amount(self):
        invalid_data = self.payment_data.copy()
        invalid_data.pop("amount")
        response = self.client.post(self.url, invalid_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["amount"][0]),
            "Este campo es requerido.",
        )

    def test_payment_create_view_with_big_amount(self):
        data = self.payment_data.copy()
        data["amount"] = Decimal("99999999.99")
        response = self.client.post(self.url, data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_payment_create_view_with_too_big_amount(self):
        data = self.payment_data.copy()
        data["amount"] = Decimal("999999991.99")
        response = self.client.post(self.url, data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["amount"][0]),
            "Asegúrese de que no haya más de 10 dígitos en total.",
        )

    def test_payment_create_view_with_no_reference(self):
        invalid_data = self.payment_data.copy()
        invalid_data.pop("reference")
        response = self.client.post(self.url, invalid_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["reference"][0]),
            "Este campo es requerido.",
        )

    def test_payment_create_view_too_long_reference(self):
        data = self.payment_data.copy()
        data["reference"] = "refg34567987654323765"
        response = self.client.post(self.url, data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["reference"][0]),
            "Asegúrese de que este campo no tenga más de 20 caracteres.",
        )

    def test_payment_create_with_duplicated_reference(self):
        PaymentFactory(reference="1234567890", dealer=self.dealer.user)
        data = self.payment_data.copy()
        data["reference"] = "1234567890"
        response = self.client.post(self.url, data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["reference"][0]),
            "Esta referencia ya existe.",
        )

    def test_payment_create_view_with_invalid_status(self):
        invalid_data = self.payment_data.copy()
        invalid_data["status"] = "invalid"
        response = self.client.post(self.url, invalid_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["status"][0]),
            '"invalid" no es una elección válida.',
        )

    def test_payment_create_view_with_no_bank(self):
        invalid_data = self.payment_data.copy()
        invalid_data.pop("bank")
        response = self.client.post(self.url, invalid_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["bank"][0]),
            "Este campo es requerido.",
        )

    def test_payment_create_view_with_invalid_bank(self):
        data = self.payment_data.copy()
        data["bank"] = "10343"
        response = self.client.post(self.url, data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["bank"][0]),
            '"10343" no es una elección válida.',
        )

    def test_payment_create_view_with_no_id_number(self):
        invalid_data = self.payment_data.copy()
        invalid_data.pop("id_number")
        response = self.client.post(self.url, invalid_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["id_number"][0]),
            "Este campo es requerido.",
        )

    def test_payment_create_view_with_no_numeric_id_number(self):
        invalid_data = self.payment_data.copy()
        invalid_data["id_number"] = "invalid"
        response = self.client.post(self.url, invalid_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["id_number"][0]),
            "Ingrese un número de cédula válido (6 hasta 8 dígitos)",
        )

    def test_payment_create_view_with_too_short_id_number(self):
        invalid_data = self.payment_data.copy()
        invalid_data["id_number"] = "12345"
        response = self.client.post(self.url, invalid_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["id_number"][0]),
            "Ingrese un número de cédula válido (6 hasta 8 dígitos)",
        )

    def test_payment_create_view_with_too_long_id_number(self):
        invalid_data = self.payment_data.copy()
        invalid_data["id_number"] = "123456789"
        response = self.client.post(self.url, invalid_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["id_number"][0]),
            "Ingrese un número de cédula válido (6 hasta 8 dígitos)",
        )

    def test_payment_create_with_invalid_payment_type(self):
        data = self.payment_data.copy()
        data["payment_type"] = "invalid"
        response = self.client.post(self.url, data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["payment_type"][0]),
            '"invalid" no es una elección válida.',
        )

    def test_payment_type_setting(self):
        data = self.payment_data.copy()
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
        cls.mobile_payment_data = {
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
        response = self.client.post(
            self.url, self.mobile_payment_data, format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(MobilePayment.objects.count(), 1)
        self.assertEqual(response.data["id"], 1)
        self.assertEqual(response.data["status"], "pending")
        self.assertEqual(response.data["dealer"], self.dealer.user.id)
        self.assertEqual(response.data["dealer_email"], self.dealer.email)
        self.assertEqual(
            response.data["payment_date"], str(self.mobile_payment_data["payment_date"])
        )
        self.assertEqual(response.data["bank"], self.mobile_payment_data["bank"])
        self.assertEqual(response.data["bank_name"], "BBVA Provincial")
        self.assertEqual(
            Decimal(response.data["amount"]), self.mobile_payment_data["amount"]
        )
        self.assertEqual(
            response.data["reference"], self.mobile_payment_data["reference"]
        )
        self.assertEqual(
            response.data["id_number"], self.mobile_payment_data["id_number"]
        )
        self.assertEqual(
            response.data["payment_type"], self.mobile_payment_data["payment_type"]
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
        response = self.client.post(
            self.url, self.mobile_payment_data, format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"], "Solo los detallistas pueden realizar esta acción"
        )

    def test_basic_user_cannot_create_mobile_payment(self):
        self.client.force_authenticate(user=self.basic_user)
        response = self.client.post(
            self.url, self.mobile_payment_data, format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"], "Solo los detallistas pueden realizar esta acción"
        )

    def test_unauthenticated_user_cannot_create_mobile_payment(self):
        self.client.logout()
        response = self.client.post(
            self.url, self.mobile_payment_data, format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Debe iniciar sesión para realizar esta acción"
        )

    def test_mobile_payment_create_view_with_no_phone_code(self):
        invalid_data = self.mobile_payment_data.copy()
        invalid_data.pop("phone_code")
        response = self.client.post(self.url, invalid_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["phone_code"][0]),
            "Este campo es requerido.",
        )

    def test_payment_create_view_with_invalid_phone_code(self):
        invalid_data = self.mobile_payment_data.copy()
        invalid_data["phone_code"] = "invalid"
        response = self.client.post(self.url, invalid_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["phone_code"][0]),
            '"invalid" no es una elección válida.',
        )

    def test_mobile_payment_create_view_with_no_phone_number(self):
        invalid_data = self.mobile_payment_data.copy()
        invalid_data.pop("phone_number")
        response = self.client.post(self.url, invalid_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["phone_number"][0]),
            "Este campo es requerido.",
        )

    def test_payment_create_view_with_no_numeric_phone_number(self):
        invalid_data = self.mobile_payment_data.copy()
        invalid_data["phone_number"] = "invalid"
        response = self.client.post(self.url, invalid_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["phone_number"][0]),
            "Ingrese un número de teléfono válido (7 dígitos)",
        )

    def test_payment_create_view_with_too_short_phone_number(self):
        invalid_data = self.mobile_payment_data.copy()
        invalid_data["phone_number"] = "123456"
        response = self.client.post(self.url, invalid_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["phone_number"][0]),
            "Ingrese un número de teléfono válido (7 dígitos)",
        )

    def test_payment_create_view_with_too_long_phone_number(self):
        invalid_data = self.mobile_payment_data.copy()
        invalid_data["phone_number"] = "12345678"
        response = self.client.post(self.url, invalid_data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["phone_number"][0]),
            "Ingrese un número de teléfono válido (7 dígitos)",
        )

    def test_payment_create_view_with_incorrect_payment_type(self):
        invalid_data = self.mobile_payment_data.copy()
        invalid_data["payment_type"] = "bank"
        response = self.client.post(self.url, invalid_data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["non_field_errors"][0]),
            "El tipo de pago debe ser 'mobile' para pagos móviles.",
        )

    def test_method_not_allowed(self):
        response = self.client.get(
            self.url, self.mobile_payment_data, format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(str(response.data["detail"]), 'Método "GET" no permitido.')
