from decimal import Decimal
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from promotions.models import Promotion
from promotions.test.factories import PromotionFactory
from editions.test.factories import EditionFactory
from authentication.test.factories import UserFactory
from users.test.factories import DealerFactory
from commerce.models import Order
from .factories import Orderfactory
from rest_framework import status
from ..serializers import OrderSerializer


class OrderListCreateAPIViewAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.promotion = PromotionFactory()
        cls.edition = EditionFactory(promotion=cls.promotion)
        cls.edition_2 = EditionFactory(
            promotion=cls.promotion, collection__name='Angela')
        cls.superuser = UserFactory(is_superuser=True)
        cls.user_dealer = UserFactory()
        cls.dealer = DealerFactory(user=cls.user_dealer)
        cls.basic_user = UserFactory()
        cls.url = reverse('order-list-create')

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
            self.assertEqual(order, OrderSerializer(
                Order.objects.get(pk=order['id'])).data)

    def test_superuser_cannot_get_order_list(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data['detail'], "Solo los detallistas pueden realizar esta acción")

    def test_basic_user_cannot_get_order_list(self):
        self.client.force_authenticate(user=self.basic_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data['detail'], "Solo los detallistas pueden realizar esta acción")

    def test_unauthorized_user_cannot_get_order_list(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data['detail'], "Debe iniciar sesión para realizar esta acción")

    def test_dealer_can_create_order(self):
        self.client.force_authenticate(user=self.dealer.user)
        data = {
            'edition': self.edition.id
        }

        response = self.client.post(self.url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, OrderSerializer(
            Order.objects.get(pk=response.data['id'])).data)

    def test_superuser_cannot_create_order(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data['detail'], "Solo los detallistas pueden realizar esta acción")

    def test_basic_user_cannot_create_order(self):
        self.client.force_authenticate(user=self.basic_user)
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data['detail'], "Solo los detallistas pueden realizar esta acción")

    def test_unauthorized_user_cannot_create_order(self):
        self.client.logout()
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data['detail'], "Debe iniciar sesión para realizar esta acción")

    def test_create_order_without_active_promotion(self):
        Promotion.objects.all().delete()
        promotion = PromotionFactory(past=True)
        edition = EditionFactory(
            promotion=promotion, collection__name='freefire')
        self.client.force_authenticate(user=self.dealer.user)
        data = {
            'edition': edition.id
        }

        response = self.client.post(self.url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data['detail'],
            'No hay ninguna promoción en curso; no se puede realizar esta acción'
        )

    def test_create_order_without_edition_id(self):
        self.client.force_authenticate(user=self.dealer.user)
        data = {}

        response = self.client.post(self.url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data['detail'],
            'El campo edition no puede estar vacío'
        )

    def test_create_order_with_invalid_edition_id(self):
        self.client.force_authenticate(user=self.dealer.user)
        data = {
            'edition': 10000
        }

        response = self.client.post(self.url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data['detail'],
            'No existe ninguna edición con el id suministrado'
        )

    def test_create_order_with_no_available_box(self):
        Orderfactory(edition=self.edition)
        self.client.force_authenticate(user=self.dealer.user)
        data = {
            'edition': self.edition.id
        }

        response = self.client.post(self.url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data['detail'], 'No hay paquetes disponibles para esta edición')

    def test_create_order_with_invalid_data_format(self):
        self.client.force_authenticate(user=self.dealer.user)
        data = "invalid_json_data"  # Esto provocará un error de parsing

        response = self.client.post(self.url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_amount_calculation(self):
        self.promotion.pack_cost = Decimal('2.50')
        self.promotion.save()
        box = self.edition.boxes.all().first()
        packs = box.packs.all().count()
        amount = self.promotion.pack_cost * packs

        self.client.force_authenticate(user=self.dealer.user)
        data = {
            'edition': self.edition.id
        }

        response = self.client.post(self.url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['amount'], str(amount))

    def test_method_not_allowed(self):
        self.client.force_authenticate(user=self.dealer.user)
        data = {
            'edition': self.edition.id
        }

        response = self.client.put(self.url, data=data, format='json')

        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data['detail'], 'Método "PUT" no permitido.')
