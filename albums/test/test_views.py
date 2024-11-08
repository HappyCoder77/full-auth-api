
from django.urls import reverse
from django.conf import settings
from rest_framework.test import (
    APIClient, APITestCase)
from rest_framework import status


from authentication.test.factories import UserFactory
from promotions.test.factories import PromotionFactory
from editions.test.factories import EditionFactory
from users.test.factories import CollectorFactory
from ..views import AlbumViewSet
from .factories import AlbumFactory


class AlbumViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.promotion = PromotionFactory()
        cls.edition = EditionFactory(promotion=cls.promotion)
        cls.superuser = UserFactory(is_superuser=True)
        cls.collector_user = UserFactory()
        cls.user = UserFactory()
        cls.collector = CollectorFactory(
            user=cls.collector_user, email=cls.user.email)
        cls.list_url = reverse('album-list')
        cls.detail_url = reverse(
            'album-detail', kwargs={'pk': cls.collector.user.pk})

    def setUp(self):
        self.album = AlbumFactory(
            collector=self.collector.user, edition=self.edition)

    def test_superuser_can_get_album_list(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        for album in response.data:
            self.assertIn('id', album)
            self.assertIn('pages', album)
            self.assertIn('collector', album)
            self.assertIn('edition', album)

    def test_collector_cannot_get_album_list(self):
        self.client.force_authenticate(user=self.collector.user)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data['detail'], "Sólo los  superusuarios pueden realizar esta acción")

    def test_basic_user_cannot_get_album_list(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data['detail'], "Sólo los  superusuarios pueden realizar esta acción")

    def test_unauthenticated_user_cannot_get_album_list(self):
        self.client.logout()
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data['detail'], "Debe estar autenticado para realizar esta acción")

    def test_collector_can_retrieve_album(self):
        self.client.force_authenticate(user=self.collector.user)
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.album.id)
        self.assertEqual(response.data['collector'], self.album.collector.id)
        self.assertEqual(response.data['edition'], self.album.edition.id)

    def test_superuser_can_retrieve_album(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.album.id)
        self.assertEqual(response.data['collector'], self.album.collector.id)
        self.assertEqual(response.data['edition'], self.album.edition.id)

    def test_basic_user_cannot_retrieve_album(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data['detail'],
            "Solo los coleccionistas o superusuarios pueden realizar esta acción"
        )

    def test_collector_cannot_retrieve_someone_else_album(self):
        collector = CollectorFactory(user=self.user)
        self.client.force_authenticate(user=collector.user)
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data['detail'],
            "Solo puedes ver tu propio álbum"
        )

    def test_unauthenticated_user_cannot_retrieve_album(self):
        self.client.logout()
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data['detail'], "Debe estar autenticado para realizar esta acción")

    def test_collector_can_create_album(self):
        # TODO: un collector no puede crear mas de 1 album por coleccion
        user = UserFactory()
        collector = CollectorFactory(user=user)
        self.client.force_authenticate(user=collector.user)
        data = {
            'collector': self.collector.user.id,
            'edition': self.edition.id
        }
        response = self.client.post(self.list_url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['collector'], collector.id)
        self.assertEqual(response.data['edition'], self.edition.id)

    def test_superuser_can_create_album(self):

        self.client.force_authenticate(user=self.superuser)
        data = {
            'collector': self.superuser.id,
            'edition': self.edition.id
        }
        response = self.client.post(self.list_url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['collector'], self.superuser.id)
        self.assertEqual(response.data['edition'], self.edition.id)

    def test_basic_user_cannot_create_album(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'collector': self.superuser.id,
            'edition': self.edition.id
        }
        response = self.client.post(self.list_url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data['detail'],
            "Solo los coleccionistas o superusuarios pueden realizar esta acción"
        )

    def test_unauthenticated_user_cannot_create_album(self):
        self.client.logout()
        data = {
            'collector': self.superuser.id,
            'edition': self.edition.id
        }
        response = self.client.post(self.list_url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data['detail'], "Debe estar autenticado para realizar esta acción")

    def test_superuser_can_update_album(self):
        # TODO: esto hay que mejorarlo, esos campos deben ser solo lectura.
        self.client.force_authenticate(user=self.superuser)
        data = {
            'collector': self.superuser.id,
            'edition': self.edition.id
        }

        response = self.client.put(self.detail_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['collector'], self.superuser.id)
        self.assertEqual(response.data['edition'], self.edition.id)

    def test_collector_cannot_update_album(self):
        self.client.force_authenticate(user=self.collector.user)
        data = {
            'collector': self.collector.user.id + 1,
            'edition': self.edition.id + 1
        }

        response = self.client.put(self.detail_url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data['detail'], "Sólo los  superusuarios pueden realizar esta acción")

    def test_basic_user_cannot_update_album(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'collector': self.collector.user.id + 1,
            'edition': self.edition.id + 1
        }

        response = self.client.put(self.detail_url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data['detail'], "Sólo los  superusuarios pueden realizar esta acción")

    def test_unauthenticated_user_cannot_update_album(self):
        self.client.logout()
        data = {
            'collector': self.collector.user.id + 1,
            'edition': self.edition.id + 1
        }

        response = self.client.put(self.detail_url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data['detail'], "Debe estar autenticado para realizar esta acción")

    def test_superuser_can_partial_update_album(self):
        # TODO: esto hay que mejorarlo, esos campos deben ser solo lectura.
        self.client.force_authenticate(user=self.superuser)
        data = {
            'collector': self.superuser.id,
            'edition': self.edition.id
        }

        response = self.client.patch(self.detail_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['collector'], self.superuser.id)
        self.assertEqual(response.data['edition'], self.edition.id)

    def test_collector_can_partial_update_album(self):
        self.client.force_authenticate(user=self.collector.user)
        data = {
            'collector': self.collector.user.id,
            'edition': self.edition.id
        }

        response = self.client.patch(self.detail_url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['collector'], self.collector.user.id)
        self.assertEqual(response.data['edition'], self.edition.id)

    def test_basic_user_cannot_partial_update_album(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'collector': self.collector.user.id,
            'edition': self.edition.id
        }

        response = self.client.patch(self.detail_url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data['detail'], "Solo los coleccionistas o superusuarios pueden realizar esta acción")

    def test_unauthenticated_user_cannot_partial_update_album(self):
        self.client.logout()
        data = {
            'collector': self.collector.user.id,
            'edition': self.edition.id
        }

        response = self.client.patch(self.detail_url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data['detail'], "Debe estar autenticado para realizar esta acción")

    def test_superuser_can_delete_album(self):
        # TODO: esto hay que mejorarlo, esos campos deben ser solo lectura.
        self.client.force_authenticate(user=self.superuser)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_collector_cannot_delete_album(self):
        self.client.force_authenticate(user=self.collector.user)

        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data['detail'], "Sólo los  superusuarios pueden realizar esta acción")

    def test_basic_user_cannot_delete_album(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.put(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data['detail'], "Sólo los  superusuarios pueden realizar esta acción")

    def test_unauthenticated_user_cannot_delete_album(self):
        self.client.logout()
        response = self.client.put(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data['detail'], "Debe estar autenticado para realizar esta acción")

    def test_http_404_handling(self):
        self.client.force_authenticate(user=self.collector.user)
        detail_url = reverse(
            'album-detail', kwargs={'pk': 110347})
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data['detail'], "No encontrado.")

    def test_method_not_allowed_handling(self):
        self.client.force_authenticate(user=self.collector.user)

        response = self.client.put(self.list_url)

        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(
            response.data['detail'], "Método no permitido.")

    def test_handle_exception_other_exception(self):
        # Crea una instancia de CollectorViewSet
        view = AlbumViewSet()

        # Simula otra excepción
        exception = ValueError("Otro tipo de error")

        # Llama al método handle_exception
        response = view.handle_exception(exception)

        # Verifica que la respuesta sea la predeterminada para otras excepciones
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(
            response.data['detail'], "Se produjo un error inesperado.")
