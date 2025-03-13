from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from albums.models import Pack
from albums.test.factories import AlbumFactory
from authentication.test.factories import UserFactory
from promotions.test.factories import PromotionFactory
from users.test.factories import CollectorFactory
from ..models import Sticker
from .factories import EditionFactory


class EditionViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.url = reverse("edition-current-list")
        cls.list_url = reverse("edition-list")
        cls.user = UserFactory()

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    def test_current_list_with_active_promotion_and_editions(self):
        PromotionFactory()
        EditionFactory(collection__theme__name="Collection 1")
        EditionFactory(collection__theme__name="Collection 2")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        expected_data = [
            {
                "id": 1,
                "collection": {
                    "id": 1,
                    "promotion": {
                        "remaining_time": "Esta promoción termina hoy a la medianoche.",
                        "max_debt": Decimal("150.00"),
                    },
                    "theme": {"name": "Collection 1", "image": None},
                },
                "circulation": "1",
            },
            {
                "id": 2,
                "collection": {
                    "id": 2,
                    "promotion": {
                        "remaining_time": "Esta promoción termina hoy a la medianoche.",
                        "max_debt": Decimal("150.00"),
                    },
                    "theme": {"name": "Collection 2", "image": None},
                },
                "circulation": "1",
            },
        ]

        self.assertEqual(response.data, expected_data)

    def test_current_list_with_active_promotion_and_no_editions(self):
        PromotionFactory()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("detail", response.data)
        self.assertEqual(
            response.data["detail"],
            "No hay ediciones activas para la promoción en curso",
        )

    def test_current_list_no_active_promotion(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("detail", response.data)
        self.assertEqual(response.data["detail"], "No hay ninguna promoción en curso")

    def test_unauthenticated_user_cannot_get_current_list(self):
        PromotionFactory()
        EditionFactory(collection__theme__name="Edition 1")
        EditionFactory(collection__theme__name="Edition 2")
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)
        self.assertEqual(
            response.data["detail"], "Debe estar autenticado para realizar esta acción"
        )

    def test_get_list(self):
        superuser = UserFactory(is_superuser=True)
        self.client.force_authenticate(user=superuser)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_only_superusers_can_get_list(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("detail", response.data)
        self.assertEqual(
            response.data["detail"],
            "Sólo los  superusuarios pueden realizar esta acción",
        )

    def test_unauthenticated_user_cannot_get_list(self):
        PromotionFactory()
        EditionFactory(collection__theme__name="Edition 1")
        EditionFactory(collection__theme__name="Edition 2")
        self.client.logout()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)
        self.assertEqual(
            response.data["detail"], "Debe estar autenticado para realizar esta acción"
        )

    def test_superuser_can_retrieve_edition(self):
        superuser = UserFactory(is_superuser=True)
        self.client.force_authenticate(user=superuser)
        PromotionFactory()
        edition = EditionFactory(collection__theme__name="Collection 1")
        detail_url = reverse("edition-detail", kwargs={"pk": edition.pk})
        expected_data = {
            "id": 1,
            "collection": {
                "id": 1,
                "promotion": {
                    "remaining_time": "Esta promoción termina hoy a la medianoche.",
                    "max_debt": Decimal("150.00"),
                },
                "theme": {"name": "Collection 1", "image": None},
            },
            "circulation": "1",
        }

        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_data)

    def test_user_cannot_retrieve_edition(self):
        PromotionFactory()
        edition = EditionFactory(collection__theme__name="Edition 1")
        detail_url = reverse("edition-detail", kwargs={"pk": edition.pk})
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_user_cannot_retrieve_edition(self):
        self.client.logout()
        PromotionFactory()
        edition = EditionFactory(collection__theme__name="Edition 1")
        detail_url = reverse("edition-detail", kwargs={"pk": edition.pk})
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Debe estar autenticado para realizar esta acción"
        )

    def test_http_404_exception(self):
        superuser = UserFactory(is_superuser=True)
        self.client.force_authenticate(user=superuser)
        detail_url = reverse("edition-detail", kwargs={"pk": 9007})
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["detail"], "No encontrado.")

    def test_method_not_allowed_exception(self):
        superuser = UserFactory(is_superuser=True)
        self.client.force_authenticate(user=superuser)
        detail_url = reverse("edition-detail", kwargs={"pk": 9007})
        response = self.client.put(detail_url)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data["detail"], "Método no permitido.")


class RescueStickerViewTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        PromotionFactory()
        cls.edition = EditionFactory()
        cls.user = UserFactory()
        cls.collector = CollectorFactory(user=UserFactory())

    def setUp(self):
        self.album = AlbumFactory(
            collector=self.collector.user, collection=self.edition.collection
        )
        packs = Pack.objects.all()

        for pack in packs:
            pack.open(self.album.collector)

        self.collector.rescue_tickets = 3
        self.collector.save()
        self.collector.refresh_from_db()
        self.client.force_authenticate(user=self.collector.user)
        self.sticker = Sticker.objects.filter(is_repeated=True).first()
        self.url = reverse("rescue-sticker", kwargs={"sticker_id": self.sticker.id})

    def test_collector_cannot_rescue_his_own_repeated_sticker(self):
        sticker = Sticker.objects.filter(is_repeated=True).first()
        url = reverse("rescue-sticker", kwargs={"sticker_id": sticker.id})
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"],
            "No puedes rescatar tus propias barajitas repetidas",
        )

    def test_user_cannot_rescue_sticker(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "Solo los coleccionistas pueden realizar esta acción",
        )

    def test_unauthenticated_user_cannot_rescue_sticker(self):
        self.client.logout()
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"],
            "Debe iniciar sesión para realizar esta acción",
        )

    def test_other_collector_can_rescue_sticker(self):
        collector = CollectorFactory(user=UserFactory())
        self.client.force_authenticate(user=collector.user)
        response = self.client.post(self.url)
        self.sticker.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.sticker.is_rescued)
        self.assertFalse(self.sticker.is_repeated)
        self.assertTrue(self.sticker.on_the_board)
        self.assertEqual(self.sticker.collector, collector.user)

    def test_other_collector_cannot_rescue_unvalid_sticker(self):
        collector = CollectorFactory(user=UserFactory())
        self.client.force_authenticate(user=collector.user)
        self.url = reverse("rescue-sticker", kwargs={"sticker_id": 9999})
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data["detail"],
            "Sticker not found",
        )

    def test_method_not_allowed(self):
        collector = CollectorFactory(user=UserFactory())
        self.client.force_authenticate(user=collector.user)
        response = self.client.get(self.url)
        self.sticker.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(
            response.data["detail"],
            'Método "GET" no permitido.',
        )
