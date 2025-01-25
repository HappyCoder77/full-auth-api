from django.db import IntegrityError
from unittest.mock import patch
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status, mixins

from authentication.test.factories import UserFactory
from collection_manager.models import SurprisePrize
from editions.models import Pack, Sticker
from editions.test.factories import EditionFactory
from promotions.models import Promotion
from promotions.test.factories import PromotionFactory
from users.test.factories import CollectorFactory

from ..models import Album, Slot
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
            if each_sticker.number > 0:
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

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data["detail"], 'Método "GET" no permitido.')


class PlaceStickerViewTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.promotion = PromotionFactory()
        cls.edition = EditionFactory(promotion=cls.promotion)
        cls.superuser = UserFactory(is_superuser=True)
        cls.basic_user = UserFactory()
        cls.collector = CollectorFactory(user=UserFactory())
        cls.album = AlbumFactory(collector=cls.collector.user, edition=cls.edition)

        cls.sticker = (
            Sticker.objects.filter(coordinate__rarity_factor=2).order_by("id").first()
        )
        cls.sticker.collector = cls.collector.user
        cls.sticker.save()
        cls.sticker.refresh_from_db()
        cls.slot = Slot.objects.filter(absolute_number=cls.sticker.number).first()
        cls.url = reverse("place-sticker", kwargs={"sticker_id": cls.sticker.pk})
        cls.data = {"slot_id": cls.slot.pk}

    def setUp(self):

        self.client.force_authenticate(user=self.collector.user)

    def test_place_sticker_success(self):
        slots = Slot.objects.filter(page__album=self.album)
        response = self.client.post(self.url, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.slot.refresh_from_db()
        self.album.refresh_from_db()
        self.assertEqual(self.slot.sticker, self.sticker)
        self.assertFalse(self.sticker.on_the_board)
        self.assertFalse(self.slot.is_empty)
        self.assertEqual(self.slot.status, "filled")
        self.assertEqual(self.album.missing_stickers, slots.count() - 1)
        self.assertEqual(self.album.collected_stickers, 1)

    def test_place_sticker_unauthorized(self):
        self.client.logout()
        response = self.client.post(self.url, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Debe iniciar sesión para realizar esta acción"
        )

    def test_superuser_cannot_place_sticker(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.post(self.url, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "Solo los coleccionistas pueden realizar esta acción",
        )

    def test_basic_user_cannot_place_sticker(self):
        self.client.force_authenticate(user=self.basic_user)
        response = self.client.post(self.url, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "Solo los coleccionistas pueden realizar esta acción",
        )

    def test_collector_cannot_place_someone_else_sticker_on_someone_else_slot(self):
        other_collector = CollectorFactory(user=UserFactory())
        self.client.force_authenticate(user=other_collector.user)
        response = self.client.post(self.url, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "Solo puedes pegar tus propias barajitas",
        )

    def test_collector_cannot_place_sticker_on_someone_else_album(self):
        other_collector = CollectorFactory(user=UserFactory())
        other_album = AlbumFactory(collector=other_collector.user, edition=self.edition)
        other_slot = Slot.objects.filter(page__album=other_album).first()
        data = {"slot_id": other_slot.pk}
        self.client.force_authenticate(user=self.collector.user)
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "Solo puedes pegar barajitas en tu propio album",
        )

    def test_place_sticker_invalid_slot_id(self):
        response = self.client.post(self.url, data={"slot_id": 99999})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Slot not found")

    def test_place_sticker_invalid_sticker_id(self):
        url = reverse("place-sticker", kwargs={"sticker_id": 99999})
        response = self.client.post(url, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Sticker not found")

    def test_place_sticker_in_filled_slot(self):
        # First placement
        self.client.post(self.url, data=self.data)

        # Create another sticker
        new_sticker = (
            Sticker.objects.filter(coordinate__rarity_factor=1)
            .exclude(id=self.sticker.pk)
            .order_by("id")
            .first()
        )
        new_sticker.collector = self.collector.user
        new_sticker.save()
        new_sticker.refresh_from_db()

        # Try to place in same slot
        url = reverse("place-sticker", kwargs={"sticker_id": new_sticker.pk})
        response = self.client.post(url, data=self.data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("ya está llena", str(response.data["error"]))


class DiscoverPrizeViewTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.promotion = PromotionFactory()
        cls.edition = EditionFactory(promotion=cls.promotion)
        cls.collector = CollectorFactory(user=UserFactory())
        cls.basic_user = UserFactory()
        cls.superuser = UserFactory(is_superuser=True)
        cls.prized_sticker = Sticker.objects.filter(
            coordinate__absolute_number=0, pack__box__edition=cls.edition
        ).first()
        cls.pack = cls.prized_sticker.pack
        cls.pack.open(cls.collector.user)
        cls.url = reverse(
            "discover-prize", kwargs={"sticker_id": cls.prized_sticker.pk}
        )

    def setUp(self):
        self.client.force_authenticate(user=self.collector.user)

    def test_discover_prize_success(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("prize", response.data)
        self.assertFalse(response.data["claimed"])
        self.assertIsNone(response.data["claimed_date"])

    def test_discover_prize_unauthorized(self):
        self.client.logout()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Debe iniciar sesión para realizar esta acción"
        )

    def test_discover_prize_basic_user(self):
        self.client.force_authenticate(user=self.basic_user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "Solo los coleccionistas pueden realizar esta acción",
        )

    def test_discover_prize_superuser(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "Solo los coleccionistas pueden realizar esta acción",
        )

    def test_discover_prize_wrong_collector(self):
        other_collector = CollectorFactory(user=UserFactory())
        self.client.force_authenticate(user=other_collector.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "Solo puedes descubrir premios de tus propias barajitas",
        )

    def test_discover_prize_non_prize_sticker(self):
        regular_sticker = Sticker.objects.filter(
            coordinate__absolute_number__gt=0
        ).first()
        pack = regular_sticker.pack
        pack.open(self.collector.user)

        url = reverse("discover-prize", kwargs={"sticker_id": regular_sticker.pk})
        response = self.client.post(url)
        # print(response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"],
            "Solo las barajitas premiadas pueden descubrir premios sorpresa",
        )

    def test_discover_prize_already_discovered(self):
        # First discovery
        self.client.post(self.url)
        # Second attempt
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"], "Esta barajita ya tiene un premio asignado"
        )

    def test_method_not_allowed(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data["detail"], 'Método "GET" no permitido.')
