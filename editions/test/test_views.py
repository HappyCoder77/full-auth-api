from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from authentication.test.factories import UserFactory
from promotions.test.factories import PromotionFactory
from .factories import EditionFactory


class EditionViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.url = reverse('edition-current-list')
        cls.list_url = reverse('edition-list')
        cls.user = UserFactory()

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    def test_current_list_with_active_promotion_and_editions(self):
        promotion = PromotionFactory()
        edition = EditionFactory(
            promotion=promotion, collection__name='Edition 1')
        edition2 = EditionFactory(
            promotion=promotion, collection__name='Edition 2')

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['promotion'], promotion.id)
        self.assertEqual(response.data[0]['collection'], edition.collection.id)
        self.assertEqual(response.data[1]['promotion'], promotion.id)
        self.assertEqual(
            response.data[1]['collection'], edition2.collection.id)

    def test_current_list_with_active_promotion_and_no_editions(self):
        PromotionFactory()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('detail', response.data)
        self.assertEqual(
            response.data['detail'], 'No hay ediciones activas para la promoción en curso')

    def test_current_list_no_active_promotion(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('detail', response.data)
        self.assertEqual(response.data['detail'],
                         'No hay ninguna promoción en curso')

    def test_unauthenticated_user_cannot_get_current_list(self):
        promotion = PromotionFactory()
        EditionFactory(
            promotion=promotion, collection__name='Edition 1')
        EditionFactory(
            promotion=promotion, collection__name='Edition 2')
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)
        self.assertEqual(
            response.data['detail'], "Debe estar autenticado para realizar esta acción")

    def test_get_list(self):
        superuser = UserFactory(is_superuser=True)
        self.client.force_authenticate(user=superuser)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_only_superusers_can_get_list(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('detail', response.data)
        self.assertEqual(
            response.data['detail'], 'Sólo los  superusuarios pueden realizar esta acción')

    def test_unauthenticated_user_cannot_get_list(self):
        promotion = PromotionFactory()
        EditionFactory(
            promotion=promotion, collection__name='Edition 1')
        EditionFactory(
            promotion=promotion, collection__name='Edition 2')
        self.client.logout()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)
        self.assertEqual(
            response.data['detail'], "Debe estar autenticado para realizar esta acción")

    def test_superuser_can_retrieve_edition(self):
        superuser = UserFactory(is_superuser=True)
        self.client.force_authenticate(user=superuser)
        promotion = PromotionFactory()
        edition = EditionFactory(
            promotion=promotion, collection__name='Edition 1')
        detail_url = reverse('edition-detail', kwargs={'pk': edition.pk})
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['promotion'], promotion.id)
        self.assertEqual(response.data['collection'], edition.collection.id)

    def test_user_cannot_retrieve_edition(self):
        promotion = PromotionFactory()
        edition = EditionFactory(
            promotion=promotion, collection__name='Edition 1')
        detail_url = reverse('edition-detail', kwargs={'pk': edition.pk})
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data['detail'], 'Sólo los  superusuarios pueden realizar esta acción')

    def test_unauthenticated_user_cannot_retrieve_edition(self):
        self.client.logout()
        promotion = PromotionFactory()
        edition = EditionFactory(
            promotion=promotion, collection__name='Edition 1')
        detail_url = reverse('edition-detail', kwargs={'pk': edition.pk})
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data['detail'], 'Debe estar autenticado para realizar esta acción')
