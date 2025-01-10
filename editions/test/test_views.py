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
        cls.url = reverse("edition-current-list")
        cls.list_url = reverse("edition-list")
        cls.user = UserFactory()

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    def test_current_list_with_active_promotion_and_editions(self):
        promotion = PromotionFactory()
        EditionFactory(promotion=promotion, collection__name="Collection 1")
        EditionFactory(promotion=promotion, collection__name="Collection 2")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        for item in response.data:
            self.assertIn("remaining_time", item["promotion"])
            self.assertIn(
                "Esta promoción termina hoy a la medianoche.",
                item["promotion"]["remaining_time"],
            )
            self.assertIn("name", item["collection"])
            self.assertIn("image", item["collection"])

        collection_names = [item["collection"]["name"] for item in response.data]
        self.assertIn("Collection 1", collection_names)
        self.assertIn("Collection 2", collection_names)

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
        promotion = PromotionFactory()
        EditionFactory(promotion=promotion, collection__name="Edition 1")
        EditionFactory(promotion=promotion, collection__name="Edition 2")
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
        promotion = PromotionFactory()
        EditionFactory(promotion=promotion, collection__name="Edition 1")
        EditionFactory(promotion=promotion, collection__name="Edition 2")
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
        promotion = PromotionFactory()
        edition = EditionFactory(promotion=promotion, collection__name="Collection 1")
        detail_url = reverse("edition-detail", kwargs={"pk": edition.pk})
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("remaining_time", response.data["promotion"])
        self.assertIn(
            "Esta promoción termina hoy a la medianoche.",
            response.data["promotion"]["remaining_time"],
        )
        self.assertIn("name", response.data["collection"])
        self.assertIn("Collection 1", response.data["collection"]["name"])
        self.assertIn("image", response.data["collection"])

    def test_user_cannot_retrieve_edition(self):
        promotion = PromotionFactory()
        edition = EditionFactory(promotion=promotion, collection__name="Edition 1")
        detail_url = reverse("edition-detail", kwargs={"pk": edition.pk})
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "Sólo los  superusuarios pueden realizar esta acción",
        )

    def test_unauthenticated_user_cannot_retrieve_edition(self):
        self.client.logout()
        promotion = PromotionFactory()
        edition = EditionFactory(promotion=promotion, collection__name="Edition 1")
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
