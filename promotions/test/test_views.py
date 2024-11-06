from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate, APIClient
from rest_framework import status
from datetime import timedelta
from django.urls import reverse
from authentication.test.factories import UserFactory
from .factories import PromotionFactory
from ..models import Promotion
from ..views import PromotionViewSet

User = get_user_model()


class PromotionViewSetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.now = timezone.now()
        self.past_promotion = PromotionFactory(past=True)
        self.future_promotion = PromotionFactory(future=True)
        self.list_url = reverse('promotion-list')
        # self.detail_url = reverse(
        #     'promotion-detail', kwargs={'pk': self.active_promotion.pk})
        self.current_url = reverse('promotion-current')

    def test_promotion_list(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_promotion_list_forbidden(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(response.data["detail"],
                        "Sólo un superusuario puede realizar esta acción.")

    def test_promotion_list_unauthorized(self):
        self.client.logout()
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(response.data["detail"],
                        "Debe estar autenticado para realizar esta acción.")

    def test_promotion_create(self):
        data = {}
        response = self.client.post(self.list_url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['remaining_time'],
                         'Esta promoción termina en 23 horas, 59 minutos y 59 segundos.')
        self.assertEqual(Promotion.objects.count(), 3)

    def test_promotion_create_forbidden(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)
        data = {}
        response = self.client.post(self.list_url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["detail"],
                         "Sólo un superusuario puede realizar esta acción.")

    def test_promotion_create_unauthorized(self):
        self.client.logout()
        data = {}
        response = self.client.post(self.list_url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["detail"],
                         "Debe estar autenticado para realizar esta acción.")

    def test_current_promotion(self):
        data = {}
        self.client.post(self.list_url, data=data, format='json')
        response = self.client.get(self.current_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["remaining_time"],
                        "Esta promoción termina en 23 horas, 59 minutos y 59 segundos")

    def test_current_promotion_with_user(self):
        user = UserFactory()
        data = {}
        self.client.post(self.list_url, data=data, format='json')
        self.client.force_authenticate(user=user)
        response = self.client.get(self.current_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["remaining_time"],
                        "Esta promoción termina en 23 horas, 59 minutos y 59 segundos")

    def test_current_promotion_unauthorized(self):
        data = {}
        self.client.post(self.list_url, data=data, format='json')
        self.client.logout()
        response = self.client.get(self.current_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(response.data["detail"],
                        "Debe estar autenticado para realizar esta acción.")

    def test_no_current_promotion(self):
        response = self.client.get(self.current_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data)

    def test_retrieve_promotion(self):
        detail_url = reverse(
            'promotion-detail', kwargs={'pk': self.past_promotion.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['remaining_time'], 'Esta promoción ha terminado.')

    def test_retrieve_promotion_forbidden(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)
        detail_url = reverse(
            'promotion-detail', kwargs={'pk': self.past_promotion.pk})
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data['detail'], 'Sólo un superusuario puede realizar esta acción.')

    def test_retrieve_promotion_unauthorized(self):
        self.client.logout()
        detail_url = reverse(
            'promotion-detail', kwargs={'pk': self.past_promotion.pk})
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data['detail'], 'Debe estar autenticado para realizar esta acción.')

    def test_update_promotion(self):
        # TODO: este test debe ser actualizado conforme se defina la politica de actualizacion
        partial_update_url = reverse(
            'promotion-detail', kwargs={'pk': self.future_promotion.pk})
        data = {}

        response = self.client.patch(
            partial_update_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_promotion_forbidden(self):
        # TODO: este test debe ser actualizado conforme se defina la politica de actualizacion
        user = UserFactory()
        self.client.force_authenticate(user=user)
        partial_update_url = reverse(
            'promotion-detail', kwargs={'pk': self.future_promotion.pk})
        data = {}

        response = self.client.patch(
            partial_update_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_promotion_unauthorized(self):
        # TODO: este test debe ser actualizado conforme se defina la politica de actualizacion
        self.client.logout()
        partial_update_url = reverse(
            'promotion-detail', kwargs={'pk': self.future_promotion.pk})
        data = {}

        response = self.client.patch(
            partial_update_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_promotion(self):
        delete_url = reverse(
            'promotion-detail', kwargs={'pk': self.future_promotion.pk})
        response = self.client.delete(delete_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Promotion.objects.count(), 1)

    def test_delete_promotion_forbidden(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)
        delete_url = reverse(
            'promotion-detail', kwargs={'pk': self.future_promotion.pk})
        response = self.client.delete(delete_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_promotion_unauthorized(self):
        self.client.logout()
        delete_url = reverse(
            'promotion-detail', kwargs={'pk': self.future_promotion.pk})
        response = self.client.delete(delete_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
