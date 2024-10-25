from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
from datetime import timedelta
from .factories import PromotionFactory
from ..models import Promotion
from ..views import PromotionViewSet

User = get_user_model()


class PromotionViewSetTestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = PromotionViewSet.as_view({'get': 'current'})
        self.url = '/api/promotion/'  # Ajusta esto a tu URL real

        self.user = User.objects.create_user(
            email='testuser@example.com', password='12345')

        # Crear algunas promociones para las pruebas
        self.now = timezone.now()
        self.active_promotion = PromotionFactory()
        self.past_promotion = PromotionFactory(past=True)
        self.future_promotion = PromotionFactory(future=True)

    def test_get_active_promotion(self):
        request = self.factory.get(self.url)
        force_authenticate(request, user=self.user)
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertTrue(response.data["remaining_time"],
                        "Esta promoción termina en 23 horas, 59 minutos y 59 segundos")

    def test_no_active_promotion(self):
        self.active_promotion.delete()
        request = self.factory.get(self.url)
        force_authenticate(request, user=self.user)
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data)
