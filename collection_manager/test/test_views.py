from decimal import Decimal
from unittest.mock import patch
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.exceptions import ErrorDetail

from authentication.test.factories import UserFactory
from users.test.factories import CollectorFactory
from promotions.models import Promotion
from ..models import Collection
from .factories import CollectionFactory, PromotionFactory


class CurrentCollectionListViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.url = reverse("current-collections")
        cls.user = UserFactory()
        cls.collector = CollectorFactory(user=UserFactory())
        PromotionFactory()
        CollectionFactory()
        CollectionFactory(theme__name="Mario")

    def setUp(self):
        self.client.force_authenticate(user=self.collector.user)

    def test_get_current_collections_success(self):
        expected_data = [
            {
                "promotion": {
                    "remaining_time": "Esta promoción termina hoy a la medianoche.",
                    "max_debt": Decimal("150.00"),
                },
                "theme": {"name": "Minecraft", "image": None},
            },
            {
                "promotion": {
                    "remaining_time": "Esta promoción termina hoy a la medianoche.",
                    "max_debt": Decimal("150.00"),
                },
                "theme": {"name": "Mario", "image": None},
            },
        ]
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data, expected_data)

    def test_get_current_collections_with_no_promotion(self):
        expected_data = {
            "detail": ErrorDetail(
                string="No hay ninguna promocion en curso.", code="not_found"
            )
        }
        Promotion.objects.all().delete()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, expected_data)

    def test_get_current_collections_with_no_collections(self):
        expected_data = {
            "detail": ErrorDetail(
                string="No se ha creado ninguna collección para la promoción en curso.",
                code="not_found",
            )
        }
        Collection.objects.all().delete()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, expected_data)

    def test_method_not_allowed(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        response = self.client.put(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_basic_user_cannot_get_collection_list(self):
        expected_data = {
            "detail": ErrorDetail(
                string="Solo los coleccionistas pueden realizar esta acción",
                code="permission denied",
            )
        }

        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, expected_data)

    def test_unauthenticated_user_cannot_get_collection_list(self):
        expected_data = {
            "detail": ErrorDetail(
                string="Debe iniciar sesión para realizar esta acción",
                code="permission denied",
            )
        }

        self.client.logout()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, expected_data)

    def test_get_collection_list_having_past_promotion(self):
        with patch("promotions.models.Promotion.objects.get_current") as mock_current:
            promotion = PromotionFactory(past=True)
            mock_current.return_value = promotion
            CollectionFactory(theme__name="Angela")

        response = self.client.get(self.url)

        self.assertEqual(len(response.data), 2)
