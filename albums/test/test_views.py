from django.db import IntegrityError
from unittest.mock import patch
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status, mixins

from authentication.test.factories import UserFactory
from editions.models import Pack
from editions.test.factories import EditionFactory
from promotions.models import Promotion
from promotions.test.factories import PromotionFactory
from users.test.factories import CollectorFactory

from ..models import Album
from ..serializers import AlbumSerializer
from .factories import AlbumFactory


class UserAlbumListRetrieveViewAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.promotion = PromotionFactory()
        cls.edition = EditionFactory(promotion=cls.promotion)
        cls.superuser = UserFactory(is_superuser=True)
        cls.user = UserFactory()
        cls.collector_user = UserFactory()
        cls.collector = CollectorFactory(
            user=cls.collector_user, email=cls.collector_user.email
        )
        cls.list_url = reverse("user-albums-list")
        cls.retrieve_url = reverse(
            "user-albums-retrieve", kwargs={"edition_id": cls.edition.id}
        )

    def setUp(self):
        self.album = AlbumFactory(collector=self.collector.user, edition=self.edition)

    def test_collector_can_get_user_album_list(self):
        self.client.force_authenticate(user=self.collector.user)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0], AlbumSerializer(self.album).data)
        for album in response.data:
            self.assertIn("id", album)
            self.assertIn("pages", album)
            self.assertIn("collector", album)
            self.assertIn("edition", album)

    def test_superuser_cannot_get_user_album_list(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "Solo los coleccionistas pueden realizar esta acción",
        )

    def test_basic_user_cannot_get_user_album_list(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "Solo los coleccionistas pueden realizar esta acción",
        )

    def test_unauthenticated_user_cannot_get_user_album_list(self):
        self.client.logout()
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Debe iniciar sesión para realizar esta acción"
        )

    def test_collector_can_get_user_album(self):
        self.client.force_authenticate(user=self.collector.user)
        response = self.client.get(self.retrieve_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, AlbumSerializer(self.album).data)

    def test_superuser_cannot_get_user_album(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(self.retrieve_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "Solo los coleccionistas pueden realizar esta acción",
        )

    def test_basic_user_cannot_get_user_album(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.retrieve_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "Solo los coleccionistas pueden realizar esta acción",
        )

    def test_unauthenticated_user_cannot_get_user_album(self):
        self.client.logout()
        response = self.client.get(self.retrieve_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Debe iniciar sesión para realizar esta acción"
        )

    def test_get_album_list_from_past_promotion(self):
        Promotion.objects.all().delete()
        promotion = PromotionFactory(past=True)
        edition_1 = EditionFactory(
            promotion=promotion, collection__name="past collection"
        )
        edition_2 = EditionFactory(
            promotion=promotion, collection__name="past collection_2"
        )
        user = UserFactory()
        collector = CollectorFactory(user=user)
        AlbumFactory(edition=edition_1, collector=collector.user)
        AlbumFactory(edition=edition_2, collector=collector.user)
        self.client.force_authenticate(user=collector.user)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["detail"],
            "No hay ninguna promoción en curso, no es posible la consulta.",
        )

    def test_get_user_album_with_invalid_edition_id(self):
        retrieve_url = reverse("user-albums-retrieve", kwargs={"edition_id": 10404})
        self.client.force_authenticate(user=self.collector.user)

        response = self.client.get(retrieve_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data["detail"], "No existe ninguna edición con el id suministrado"
        )

    def test_method_not_allowed_list_url(self):
        self.client.force_authenticate(user=self.collector.user)
        response = self.client.post(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_method_not_allowed_retrieve_url(self):
        self.client.force_authenticate(user=self.collector.user)
        response = self.client.post(self.retrieve_url)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class UserAlbumCreateViewAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.promotion = PromotionFactory()
        cls.edition = EditionFactory(promotion=cls.promotion)
        cls.superuser = UserFactory(is_superuser=True)
        cls.user = UserFactory()
        cls.collector_user = UserFactory()
        cls.collector = CollectorFactory(
            user=cls.collector_user, email=cls.collector_user.email
        )
        cls.url = reverse("user-albums-create")

    def test_collector_can_create_album(self):
        self.client.force_authenticate(user=self.collector.user)
        data = {"edition": self.edition.id}
        response = self.client.post(self.url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, AlbumSerializer(Album.objects.get(pk=1)).data)

    def test_collector_can_get_album_if_already_exists(self):
        AlbumFactory(edition=self.edition, collector=self.collector.user)
        self.client.force_authenticate(user=self.collector.user)
        data = {"edition": self.edition.id}
        response = self.client.post(self.url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, AlbumSerializer(Album.objects.get(pk=1)).data)

    def test_superuser_cannot_create_album(self):
        self.client.force_authenticate(user=self.superuser)
        data = {"edition": self.edition.id}
        response = self.client.post(self.url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "Solo los coleccionistas pueden realizar esta acción",
        )

    def test_basic_user_cannot_create_album(self):
        self.client.force_authenticate(user=self.user)
        data = {"edition": self.edition.id}
        response = self.client.post(self.url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "Solo los coleccionistas pueden realizar esta acción",
        )

    def test_unauthenticated_user_cannot_create_album(self):
        self.client.logout()
        data = {"edition": self.edition.id}
        response = self.client.post(self.url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Debe iniciar sesión para realizar esta acción"
        )

    def test_create_album_from_past_promotion(self):
        Promotion.objects.all().delete()
        promotion = PromotionFactory(past=True)
        edition = EditionFactory(
            promotion=promotion, collection__name="past collection"
        )
        data = {"edition": edition.id}
        self.client.force_authenticate(user=self.collector.user)
        response = self.client.post(self.url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["detail"],
            "No hay ninguna promoción en curso, no es posible esta acción.",
        )

    def test_create_album_from_future_promotion(self):
        Promotion.objects.all().delete()
        promotion = PromotionFactory(future=True)
        edition = EditionFactory(
            promotion=promotion, collection__name="future collection"
        )
        data = {"edition": edition.id}
        self.client.force_authenticate(user=self.collector.user)
        response = self.client.post(self.url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["detail"],
            "No hay ninguna promoción en curso, no es posible esta acción.",
        )

    def test_create_album_with_invalid_id(self):
        data = {"edition": 1059}
        self.client.force_authenticate(user=self.collector.user)
        response = self.client.post(self.url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data["detail"], "No existe ninguna edición con el id suministrado."
        )

    def test_create_album_with_no_id(self):
        data = {}
        self.client.force_authenticate(user=self.collector.user)
        response = self.client.post(self.url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "El campo edition es requerido.")

    def test_integrity_error_handling(self):
        self.client.force_authenticate(user=self.collector.user)
        data = {"edition": self.edition.id}

        with patch.object(mixins.CreateModelMixin, "create") as mock_create:
            mock_create.side_effect = IntegrityError("Duplicate entry")
            response = self.client.post(self.url, data=data, format="json")

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(
                response.data["detail"], "El álbum ya existe para esta edición."
            )

    def test_handle_generic_exception(self):
        self.client.force_authenticate(user=self.collector.user)
        data = {"edition": self.edition.id}

        with patch.object(mixins.CreateModelMixin, "create") as mock_create:
            mock_create.side_effect = ValueError("Some unexpected error")
            response = self.client.post(self.url, data=data, format="json")

            self.assertEqual(
                response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            self.assertEqual(response.data["detail"], "Some unexpected error")


class AlbumDetailViewTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.promotion = PromotionFactory()
        cls.edition = EditionFactory(promotion=cls.promotion)
        cls.superuser = UserFactory(is_superuser=True)
        cls.basic_user = UserFactory()
        cls.collector = CollectorFactory(user=UserFactory())
        pack = Pack.objects.first()
        pack.collector = cls.collector.user
        cls.album = Album.objects.create(
            collector=cls.collector.user, edition=cls.edition
        )
        cls.url = reverse("album-detail", kwargs={"pk": cls.album.pk})

    def setUp(self):
        self.client.force_authenticate(user=self.collector.user)

    def test_get_album_success(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, AlbumSerializer(Album.objects.get(pk=1)).data)

    def test_get_album_unauthorized(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Debe iniciar sesión para realizar esta acción"
        )

    def test_superuser_cannot_get_user_album(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "Solo los coleccionistas pueden realizar esta acción",
        )

    def test_basic_user_cannot_get_user_album(self):
        self.client.force_authenticate(user=self.basic_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "Solo los coleccionistas pueden realizar esta acción",
        )

    def test_other_collector_cannot_get_album(self):
        other_collector = CollectorFactory(user=UserFactory())
        self.client.force_authenticate(user=other_collector.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_method_not_allowed(self):
        self.client.force_authenticate(user=self.collector.user)
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class OpenPackViewTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.promotion = PromotionFactory()
        cls.edition = EditionFactory(promotion=cls.promotion)
        cls.superuser = UserFactory(is_superuser=True)
        cls.basic_user = UserFactory()
        cls.collector = CollectorFactory(user=UserFactory())
        cls.pack = Pack.objects.first()
        cls.pack.collector = cls.collector.user
        cls.pack.save()
        cls.url = reverse("open-pack", kwargs={"pk": cls.pack.pk})

    def setUp(self):
        self.client.force_authenticate(user=self.collector.user)

    def test_open_pack_success(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.pack.refresh_from_db()
        self.assertTrue(self.pack.is_open)

        for each_sticker in self.pack.stickers.all():
            self.assertEqual(each_sticker.collector, self.collector.user)
            self.assertTrue(each_sticker.on_the_board)

    def test_open_pack_unauthorized(self):
        self.client.logout()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Debe iniciar sesión para realizar esta acción"
        )

    def test_superuser_cannot_open_pack(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "Solo los coleccionistas pueden realizar esta acción",
        )

    def test_basic_user_cannot_open_pack(self):
        self.client.force_authenticate(user=self.basic_user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "Solo los coleccionistas pueden realizar esta acción",
        )

    def test_collector_cannot_open_someone_else_pack(self):
        other_collector = CollectorFactory(user=UserFactory())
        self.client.force_authenticate(user=other_collector.user)
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data["detail"],
            "El sobre que se intenta abrir no existe, pertenece a otro coleccionista o ya fué abierto",
        )

    def test_open_non_existent_pack(self):
        url = reverse("open-pack", kwargs={"pk": 1003})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data["detail"],
            "El sobre que se intenta abrir no existe, pertenece a otro coleccionista o ya fué abierto",
        )

    def test_open_already_opened_pack(self):
        self.pack.open(self.collector.user)
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response.data["detail"],
        self.assertEqual(
            response.data["detail"],
            "El sobre que se intenta abrir no existe, pertenece a otro coleccionista o ya fué abierto",
        )

    def test_method_not_allowed(self):
        response = self.client.get(self.url)
        print(response)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data["detail"], 'Método "GET" no permitido.')
