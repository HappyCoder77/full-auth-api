import os
import shutil
from django.test.utils import override_settings
import tempfile

from rest_framework.test import APIRequestFactory, force_authenticate
from albums.views import RescuePoolView
from django.db import IntegrityError, models
from unittest.mock import patch
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status, mixins
from authentication.test.factories import UserFactory
from collection_manager.test.factories import CollectionFactory, AlbumTemplateFactory
from collection_manager.models import Coordinate, Collection
from editions.models import Pack, Sticker
from editions.test.factories import EditionFactory
from promotions.models import Promotion
from promotions.test.factories import PromotionFactory
from users.test.factories import CollectorFactory

from ..models import Album, Slot, Page
from ..serializers import AlbumSerializer
from .factories import AlbumFactory

TEMP_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class UserAlbumListRetrieveViewAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        PromotionFactory()
        collection = CollectionFactory(
            album_template__with_coordinate_images=True, with_prizes_defined=True
        )
        cls.edition = EditionFactory(collection=collection)
        cls.superuser = UserFactory(is_superuser=True)
        cls.user = UserFactory()
        cls.collector_user = UserFactory()
        cls.collector = CollectorFactory(
            user=cls.collector_user, email=cls.collector_user.email
        )
        cls.list_url = reverse("user-albums-list")
        cls.retrieve_url = reverse(
            "user-albums-retrieve", kwargs={"collection_id": cls.edition.collection.id}
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.album = AlbumFactory(
            collector=self.collector.user, collection=self.edition.collection
        )

    def test_collector_can_get_user_album_list(self):
        expected_data = [
            {
                "id": 1,
                "collection": 1,
                "image": None,
                "collector": 3,
                "pages": [
                    {
                        "id": 1,
                        "page_prize": None,
                        "number": 1,
                        "slots": [
                            {
                                "id": 1,
                                "number": 1,
                                "absolute_number": 1,
                                "image": "http://testserver/media/images/coordinates/coordinate_1_1.png",
                                "is_empty": True,
                            },
                            {
                                "id": 2,
                                "number": 2,
                                "absolute_number": 2,
                                "image": "http://testserver/media/images/coordinates/coordinate_1_2.png",
                                "is_empty": True,
                            },
                            {
                                "id": 3,
                                "number": 3,
                                "absolute_number": 3,
                                "image": "http://testserver/media/images/coordinates/coordinate_1_3.png",
                                "is_empty": True,
                            },
                            {
                                "id": 4,
                                "number": 4,
                                "absolute_number": 4,
                                "image": "http://testserver/media/images/coordinates/coordinate_1_4.png",
                                "is_empty": True,
                            },
                            {
                                "id": 5,
                                "number": 5,
                                "absolute_number": 5,
                                "image": "http://testserver/media/images/coordinates/coordinate_1_5.png",
                                "is_empty": True,
                            },
                            {
                                "id": 6,
                                "number": 6,
                                "absolute_number": 6,
                                "image": "http://testserver/media/images/coordinates/coordinate_1_6.png",
                                "is_empty": True,
                            },
                        ],
                        "is_full": False,
                        "prize_was_claimed": False,
                    },
                    {
                        "id": 2,
                        "page_prize": None,
                        "number": 2,
                        "slots": [
                            {
                                "id": 7,
                                "number": 1,
                                "absolute_number": 7,
                                "image": "http://testserver/media/images/coordinates/coordinate_2_1.png",
                                "is_empty": True,
                            },
                            {
                                "id": 8,
                                "number": 2,
                                "absolute_number": 8,
                                "image": "http://testserver/media/images/coordinates/coordinate_2_2.png",
                                "is_empty": True,
                            },
                            {
                                "id": 9,
                                "number": 3,
                                "absolute_number": 9,
                                "image": "http://testserver/media/images/coordinates/coordinate_2_3.png",
                                "is_empty": True,
                            },
                            {
                                "id": 10,
                                "number": 4,
                                "absolute_number": 10,
                                "image": "http://testserver/media/images/coordinates/coordinate_2_4.png",
                                "is_empty": True,
                            },
                            {
                                "id": 11,
                                "number": 5,
                                "absolute_number": 11,
                                "image": "http://testserver/media/images/coordinates/coordinate_2_5.png",
                                "is_empty": True,
                            },
                            {
                                "id": 12,
                                "number": 6,
                                "absolute_number": 12,
                                "image": "http://testserver/media/images/coordinates/coordinate_2_6.png",
                                "is_empty": True,
                            },
                        ],
                        "is_full": False,
                        "prize_was_claimed": False,
                    },
                    {
                        "id": 3,
                        "page_prize": None,
                        "number": 3,
                        "slots": [
                            {
                                "id": 13,
                                "number": 1,
                                "absolute_number": 13,
                                "image": "http://testserver/media/images/coordinates/coordinate_3_1.png",
                                "is_empty": True,
                            },
                            {
                                "id": 14,
                                "number": 2,
                                "absolute_number": 14,
                                "image": "http://testserver/media/images/coordinates/coordinate_3_2.png",
                                "is_empty": True,
                            },
                            {
                                "id": 15,
                                "number": 3,
                                "absolute_number": 15,
                                "image": "http://testserver/media/images/coordinates/coordinate_3_3.png",
                                "is_empty": True,
                            },
                            {
                                "id": 16,
                                "number": 4,
                                "absolute_number": 16,
                                "image": "http://testserver/media/images/coordinates/coordinate_3_4.png",
                                "is_empty": True,
                            },
                            {
                                "id": 17,
                                "number": 5,
                                "absolute_number": 17,
                                "image": "http://testserver/media/images/coordinates/coordinate_3_5.png",
                                "is_empty": True,
                            },
                            {
                                "id": 18,
                                "number": 6,
                                "absolute_number": 18,
                                "image": "http://testserver/media/images/coordinates/coordinate_3_6.png",
                                "is_empty": True,
                            },
                        ],
                        "is_full": False,
                        "prize_was_claimed": False,
                    },
                    {
                        "id": 4,
                        "page_prize": None,
                        "number": 4,
                        "slots": [
                            {
                                "id": 19,
                                "number": 1,
                                "absolute_number": 19,
                                "image": "http://testserver/media/images/coordinates/coordinate_4_1.png",
                                "is_empty": True,
                            },
                            {
                                "id": 20,
                                "number": 2,
                                "absolute_number": 20,
                                "image": "http://testserver/media/images/coordinates/coordinate_4_2.png",
                                "is_empty": True,
                            },
                            {
                                "id": 21,
                                "number": 3,
                                "absolute_number": 21,
                                "image": "http://testserver/media/images/coordinates/coordinate_4_3.png",
                                "is_empty": True,
                            },
                            {
                                "id": 22,
                                "number": 4,
                                "absolute_number": 22,
                                "image": "http://testserver/media/images/coordinates/coordinate_4_4.png",
                                "is_empty": True,
                            },
                            {
                                "id": 23,
                                "number": 5,
                                "absolute_number": 23,
                                "image": "http://testserver/media/images/coordinates/coordinate_4_5.png",
                                "is_empty": True,
                            },
                            {
                                "id": 24,
                                "number": 6,
                                "absolute_number": 24,
                                "image": "http://testserver/media/images/coordinates/coordinate_4_6.png",
                                "is_empty": True,
                            },
                        ],
                        "is_full": False,
                        "prize_was_claimed": False,
                    },
                ],
                "pack_inbox": None,
                "stickers_on_the_board": None,
                "prized_stickers": [],
            }
        ]

        self.client.force_authenticate(user=self.collector.user)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data, expected_data)

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
        expected_data = {
            "id": 1,
            "collection": 1,
            "image": None,
            "collector": 3,
            "pages": [
                {
                    "id": 1,
                    "page_prize": None,
                    "number": 1,
                    "slots": [
                        {
                            "id": 1,
                            "number": 1,
                            "absolute_number": 1,
                            "image": "http://testserver/media/images/coordinates/coordinate_1_1.png",
                            "is_empty": True,
                        },
                        {
                            "id": 2,
                            "number": 2,
                            "absolute_number": 2,
                            "image": "http://testserver/media/images/coordinates/coordinate_1_2.png",
                            "is_empty": True,
                        },
                        {
                            "id": 3,
                            "number": 3,
                            "absolute_number": 3,
                            "image": "http://testserver/media/images/coordinates/coordinate_1_3.png",
                            "is_empty": True,
                        },
                        {
                            "id": 4,
                            "number": 4,
                            "absolute_number": 4,
                            "image": "http://testserver/media/images/coordinates/coordinate_1_4.png",
                            "is_empty": True,
                        },
                        {
                            "id": 5,
                            "number": 5,
                            "absolute_number": 5,
                            "image": "http://testserver/media/images/coordinates/coordinate_1_5.png",
                            "is_empty": True,
                        },
                        {
                            "id": 6,
                            "number": 6,
                            "absolute_number": 6,
                            "image": "http://testserver/media/images/coordinates/coordinate_1_6.png",
                            "is_empty": True,
                        },
                    ],
                    "is_full": False,
                    "prize_was_claimed": False,
                },
                {
                    "id": 2,
                    "page_prize": None,
                    "number": 2,
                    "slots": [
                        {
                            "id": 7,
                            "number": 1,
                            "absolute_number": 7,
                            "image": "http://testserver/media/images/coordinates/coordinate_2_1.png",
                            "is_empty": True,
                        },
                        {
                            "id": 8,
                            "number": 2,
                            "absolute_number": 8,
                            "image": "http://testserver/media/images/coordinates/coordinate_2_2.png",
                            "is_empty": True,
                        },
                        {
                            "id": 9,
                            "number": 3,
                            "absolute_number": 9,
                            "image": "http://testserver/media/images/coordinates/coordinate_2_3.png",
                            "is_empty": True,
                        },
                        {
                            "id": 10,
                            "number": 4,
                            "absolute_number": 10,
                            "image": "http://testserver/media/images/coordinates/coordinate_2_4.png",
                            "is_empty": True,
                        },
                        {
                            "id": 11,
                            "number": 5,
                            "absolute_number": 11,
                            "image": "http://testserver/media/images/coordinates/coordinate_2_5.png",
                            "is_empty": True,
                        },
                        {
                            "id": 12,
                            "number": 6,
                            "absolute_number": 12,
                            "image": "http://testserver/media/images/coordinates/coordinate_2_6.png",
                            "is_empty": True,
                        },
                    ],
                    "is_full": False,
                    "prize_was_claimed": False,
                },
                {
                    "id": 3,
                    "page_prize": None,
                    "number": 3,
                    "slots": [
                        {
                            "id": 13,
                            "number": 1,
                            "absolute_number": 13,
                            "image": "http://testserver/media/images/coordinates/coordinate_3_1.png",
                            "is_empty": True,
                        },
                        {
                            "id": 14,
                            "number": 2,
                            "absolute_number": 14,
                            "image": "http://testserver/media/images/coordinates/coordinate_3_2.png",
                            "is_empty": True,
                        },
                        {
                            "id": 15,
                            "number": 3,
                            "absolute_number": 15,
                            "image": "http://testserver/media/images/coordinates/coordinate_3_3.png",
                            "is_empty": True,
                        },
                        {
                            "id": 16,
                            "number": 4,
                            "absolute_number": 16,
                            "image": "http://testserver/media/images/coordinates/coordinate_3_4.png",
                            "is_empty": True,
                        },
                        {
                            "id": 17,
                            "number": 5,
                            "absolute_number": 17,
                            "image": "http://testserver/media/images/coordinates/coordinate_3_5.png",
                            "is_empty": True,
                        },
                        {
                            "id": 18,
                            "number": 6,
                            "absolute_number": 18,
                            "image": "http://testserver/media/images/coordinates/coordinate_3_6.png",
                            "is_empty": True,
                        },
                    ],
                    "is_full": False,
                    "prize_was_claimed": False,
                },
                {
                    "id": 4,
                    "page_prize": None,
                    "number": 4,
                    "slots": [
                        {
                            "id": 19,
                            "number": 1,
                            "absolute_number": 19,
                            "image": "http://testserver/media/images/coordinates/coordinate_4_1.png",
                            "is_empty": True,
                        },
                        {
                            "id": 20,
                            "number": 2,
                            "absolute_number": 20,
                            "image": "http://testserver/media/images/coordinates/coordinate_4_2.png",
                            "is_empty": True,
                        },
                        {
                            "id": 21,
                            "number": 3,
                            "absolute_number": 21,
                            "image": "http://testserver/media/images/coordinates/coordinate_4_3.png",
                            "is_empty": True,
                        },
                        {
                            "id": 22,
                            "number": 4,
                            "absolute_number": 22,
                            "image": "http://testserver/media/images/coordinates/coordinate_4_4.png",
                            "is_empty": True,
                        },
                        {
                            "id": 23,
                            "number": 5,
                            "absolute_number": 23,
                            "image": "http://testserver/media/images/coordinates/coordinate_4_5.png",
                            "is_empty": True,
                        },
                        {
                            "id": 24,
                            "number": 6,
                            "absolute_number": 24,
                            "image": "http://testserver/media/images/coordinates/coordinate_4_6.png",
                            "is_empty": True,
                        },
                    ],
                    "is_full": False,
                    "prize_was_claimed": False,
                },
            ],
            "pack_inbox": None,
            "stickers_on_the_board": None,
            "prized_stickers": [],
        }
        self.client.force_authenticate(user=self.collector.user)
        response = self.client.get(self.retrieve_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_data)

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
        template = AlbumTemplateFactory(with_coordinate_images=True, name="Mario")
        template_2 = AlbumTemplateFactory(with_coordinate_images=True, name="Angela")
        promotion = PromotionFactory(past=True)

        def custom_save(collection, *args, **kwargs):
            models.Model.save(collection, *args, **kwargs)
            collection.create_standard_prizes()
            collection.create_surprise_prizes()

        with patch("promotions.models.Promotion.objects.get_current") as mock_current:
            mock_current.return_value = promotion

            with patch("collection_manager.models.Collection.save") as mock_save:
                collection_1 = Collection(album_template=template)

            mock_save.side_effect = lambda *args, **kwargs: custom_save(
                collection_1, *args, **kwargs
            )
            collection_1.save()

            for prize in collection_1.surprise_prizes.all():
                prize.description = "A  surprise prize"
                prize.save()

            for prize in collection_1.standard_prizes.all():
                prize.description = "A standard prize"
                prize.save()

            EditionFactory(collection=collection_1)

            collection_2 = Collection(
                album_template=template_2,
            )

            mock_save.side_effect = lambda *args, **kwargs: custom_save(
                collection_2, *args, **kwargs
            )

            collection_2.save()

            for prize in collection_2.surprise_prizes.all():
                prize.description = "A  surprise prize"
                prize.save()

            for prize in collection_2.standard_prizes.all():
                prize.description = "A standard prize"
                prize.save()

            EditionFactory(collection=collection_2)
            user = UserFactory()
            collector = CollectorFactory(user=user)
            AlbumFactory(collection=collection_1, collector=collector.user)
            AlbumFactory(collection=collection_2, collector=collector.user)

        self.client.force_authenticate(user=collector.user)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["detail"],
            "No hay ninguna promoción en curso, no es posible la consulta.",
        )

    def test_get_user_album_with_invalid_edition_id(self):
        retrieve_url = reverse("user-albums-retrieve", kwargs={"collection_id": 10404})
        self.client.force_authenticate(user=self.collector.user)

        response = self.client.get(retrieve_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data["detail"],
            "No existe ninguna colección con el id suministrado",
        )

    def test_method_not_allowed_list_url(self):
        self.client.force_authenticate(user=self.collector.user)
        response = self.client.post(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_method_not_allowed_retrieve_url(self):
        self.client.force_authenticate(user=self.collector.user)
        response = self.client.post(self.retrieve_url)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class UserAlbumCreateViewAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        PromotionFactory()
        collection = CollectionFactory(
            album_template__with_coordinate_images=True, with_prizes_defined=True
        )
        cls.edition = EditionFactory(collection=collection)
        cls.superuser = UserFactory(is_superuser=True)
        cls.user = UserFactory()
        cls.collector_user = UserFactory()
        cls.collector = CollectorFactory(
            user=cls.collector_user, email=cls.collector_user.email
        )
        cls.url = reverse("user-albums-create")
        cls.expected_data = {
            "id": 1,
            "collection": collection.id,
            "image": None,
            "collector": cls.collector.user.id,
            "pages": [
                {
                    "id": 1,
                    "page_prize": None,
                    "number": 1,
                    "slots": [
                        {
                            "id": 1,
                            "number": 1,
                            "absolute_number": 1,
                            "image": "http://testserver/media/images/coordinates/coordinate_1_1.png",
                            "is_empty": True,
                        },
                        {
                            "id": 2,
                            "number": 2,
                            "absolute_number": 2,
                            "image": "http://testserver/media/images/coordinates/coordinate_1_2.png",
                            "is_empty": True,
                        },
                        {
                            "id": 3,
                            "number": 3,
                            "absolute_number": 3,
                            "image": "http://testserver/media/images/coordinates/coordinate_1_3.png",
                            "is_empty": True,
                        },
                        {
                            "id": 4,
                            "number": 4,
                            "absolute_number": 4,
                            "image": "http://testserver/media/images/coordinates/coordinate_1_4.png",
                            "is_empty": True,
                        },
                        {
                            "id": 5,
                            "number": 5,
                            "absolute_number": 5,
                            "image": "http://testserver/media/images/coordinates/coordinate_1_5.png",
                            "is_empty": True,
                        },
                        {
                            "id": 6,
                            "number": 6,
                            "absolute_number": 6,
                            "image": "http://testserver/media/images/coordinates/coordinate_1_6.png",
                            "is_empty": True,
                        },
                    ],
                    "is_full": False,
                    "prize_was_claimed": False,
                },
                {
                    "id": 2,
                    "page_prize": None,
                    "number": 2,
                    "slots": [
                        {
                            "id": 7,
                            "number": 1,
                            "absolute_number": 7,
                            "image": "http://testserver/media/images/coordinates/coordinate_2_1.png",
                            "is_empty": True,
                        },
                        {
                            "id": 8,
                            "number": 2,
                            "absolute_number": 8,
                            "image": "http://testserver/media/images/coordinates/coordinate_2_2.png",
                            "is_empty": True,
                        },
                        {
                            "id": 9,
                            "number": 3,
                            "absolute_number": 9,
                            "image": "http://testserver/media/images/coordinates/coordinate_2_3.png",
                            "is_empty": True,
                        },
                        {
                            "id": 10,
                            "number": 4,
                            "absolute_number": 10,
                            "image": "http://testserver/media/images/coordinates/coordinate_2_4.png",
                            "is_empty": True,
                        },
                        {
                            "id": 11,
                            "number": 5,
                            "absolute_number": 11,
                            "image": "http://testserver/media/images/coordinates/coordinate_2_5.png",
                            "is_empty": True,
                        },
                        {
                            "id": 12,
                            "number": 6,
                            "absolute_number": 12,
                            "image": "http://testserver/media/images/coordinates/coordinate_2_6.png",
                            "is_empty": True,
                        },
                    ],
                    "is_full": False,
                    "prize_was_claimed": False,
                },
                {
                    "id": 3,
                    "page_prize": None,
                    "number": 3,
                    "slots": [
                        {
                            "id": 13,
                            "number": 1,
                            "absolute_number": 13,
                            "image": "http://testserver/media/images/coordinates/coordinate_3_1.png",
                            "is_empty": True,
                        },
                        {
                            "id": 14,
                            "number": 2,
                            "absolute_number": 14,
                            "image": "http://testserver/media/images/coordinates/coordinate_3_2.png",
                            "is_empty": True,
                        },
                        {
                            "id": 15,
                            "number": 3,
                            "absolute_number": 15,
                            "image": "http://testserver/media/images/coordinates/coordinate_3_3.png",
                            "is_empty": True,
                        },
                        {
                            "id": 16,
                            "number": 4,
                            "absolute_number": 16,
                            "image": "http://testserver/media/images/coordinates/coordinate_3_4.png",
                            "is_empty": True,
                        },
                        {
                            "id": 17,
                            "number": 5,
                            "absolute_number": 17,
                            "image": "http://testserver/media/images/coordinates/coordinate_3_5.png",
                            "is_empty": True,
                        },
                        {
                            "id": 18,
                            "number": 6,
                            "absolute_number": 18,
                            "image": "http://testserver/media/images/coordinates/coordinate_3_6.png",
                            "is_empty": True,
                        },
                    ],
                    "is_full": False,
                    "prize_was_claimed": False,
                },
                {
                    "id": 4,
                    "page_prize": None,
                    "number": 4,
                    "slots": [
                        {
                            "id": 19,
                            "number": 1,
                            "absolute_number": 19,
                            "image": "http://testserver/media/images/coordinates/coordinate_4_1.png",
                            "is_empty": True,
                        },
                        {
                            "id": 20,
                            "number": 2,
                            "absolute_number": 20,
                            "image": "http://testserver/media/images/coordinates/coordinate_4_2.png",
                            "is_empty": True,
                        },
                        {
                            "id": 21,
                            "number": 3,
                            "absolute_number": 21,
                            "image": "http://testserver/media/images/coordinates/coordinate_4_3.png",
                            "is_empty": True,
                        },
                        {
                            "id": 22,
                            "number": 4,
                            "absolute_number": 22,
                            "image": "http://testserver/media/images/coordinates/coordinate_4_4.png",
                            "is_empty": True,
                        },
                        {
                            "id": 23,
                            "number": 5,
                            "absolute_number": 23,
                            "image": "http://testserver/media/images/coordinates/coordinate_4_5.png",
                            "is_empty": True,
                        },
                        {
                            "id": 24,
                            "number": 6,
                            "absolute_number": 24,
                            "image": "http://testserver/media/images/coordinates/coordinate_4_6.png",
                            "is_empty": True,
                        },
                    ],
                    "is_full": False,
                    "prize_was_claimed": False,
                },
            ],
            "pack_inbox": None,
            "stickers_on_the_board": None,
            "prized_stickers": [],
        }

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_collector_can_create_album(self):

        self.client.force_authenticate(user=self.collector.user)
        data = {"collection": self.edition.collection.id}
        response = self.client.post(self.url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, self.expected_data)

    def test_collector_can_get_album_if_already_exists(self):
        AlbumFactory(collector=self.collector.user, collection=self.edition.collection)
        self.client.force_authenticate(user=self.collector.user)
        data = {"collection": self.edition.collection.id}
        response = self.client.post(self.url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, self.expected_data)

    def test_superuser_cannot_create_album(self):
        self.client.force_authenticate(user=self.superuser)
        data = {"collection": self.edition.collection.id}
        response = self.client.post(self.url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "Solo los coleccionistas pueden realizar esta acción",
        )

    def test_basic_user_cannot_create_album(self):
        self.client.force_authenticate(user=self.user)
        data = {"collection": self.edition.collection.id}
        response = self.client.post(self.url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "Solo los coleccionistas pueden realizar esta acción",
        )

    def test_unauthenticated_user_cannot_create_album(self):
        self.client.logout()
        data = {"collection": self.edition.collection.id}
        response = self.client.post(self.url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Debe iniciar sesión para realizar esta acción"
        )

    def test_create_album_from_past_promotion(self):
        Promotion.objects.all().delete()
        promotion = PromotionFactory(past=True)

        with patch("collection_manager.models.Collection.save") as mock_save:
            collection = Collection.objects.create(
                promotion=promotion,
            )

            mock_save.side_effect = lambda *args, **kwargs: models.Model.save(
                Collection, *args, **kwargs
            )
            data = {"collection": collection.id}
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
        with patch("collection_manager.models.Collection.save") as mock_save:
            collection = Collection.objects.create(
                promotion=promotion,
            )
            mock_save.side_effect = lambda *args, **kwargs: models.Model.save(
                collection, *args, **kwargs
            )
            data = {"collection": collection.id}
            self.client.force_authenticate(user=self.collector.user)
            response = self.client.post(self.url, data=data, format="json")

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(
                response.data["detail"],
                "No hay ninguna promoción en curso, no es posible esta acción.",
            )

    def test_create_album_with_invalid_id(self):
        data = {"collection": 1059}
        self.client.force_authenticate(user=self.collector.user)
        response = self.client.post(self.url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data["detail"],
            "No existe ninguna colección con el id suministrado.",
        )

    def test_create_album_with_no_id(self):
        data = {}
        self.client.force_authenticate(user=self.collector.user)
        response = self.client.post(self.url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "El campo collection es requerido.")

    def test_integrity_error_handling(self):
        self.client.force_authenticate(user=self.collector.user)
        data = {"collection": self.edition.collection.id}

        with patch.object(mixins.CreateModelMixin, "create") as mock_create:
            mock_create.side_effect = IntegrityError("Duplicate entry")
            response = self.client.post(self.url, data=data, format="json")

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(
                response.data["detail"], "El álbum ya existe para esta edición."
            )

    def test_handle_generic_exception(self):
        self.client.force_authenticate(user=self.collector.user)
        data = {"collection": self.edition.collection.id}

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
        PromotionFactory()
        collection = CollectionFactory()
        cls.superuser = UserFactory(is_superuser=True)
        cls.basic_user = UserFactory()
        cls.collector = CollectorFactory(user=UserFactory())
        cls.album = Album.objects.create(
            collector=cls.collector.user, collection=collection
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


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class OpenPackViewTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        PromotionFactory()
        collection = CollectionFactory(
            album_template__with_coordinate_images=True, with_prizes_defined=True
        )
        cls.edition = EditionFactory(collection=collection)
        cls.superuser = UserFactory(is_superuser=True)
        cls.basic_user = UserFactory()
        cls.collector = CollectorFactory(user=UserFactory())
        cls.pack = Pack.objects.first()
        cls.pack.collector = cls.collector.user
        cls.pack.save()
        cls.url = reverse("open-pack", kwargs={"pk": cls.pack.pk})

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

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


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PlaceStickerViewTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        PromotionFactory()
        collection = CollectionFactory(
            album_template__with_coordinate_images=True, with_prizes_defined=True
        )
        cls.edition = EditionFactory(collection=collection)
        cls.superuser = UserFactory(is_superuser=True)
        cls.basic_user = UserFactory()
        cls.collector = CollectorFactory(user=UserFactory())
        cls.album = AlbumFactory(collector=cls.collector.user, collection=collection)

        cls.sticker = (
            Sticker.objects.filter(coordinate__rarity_factor=2).order_by("id").first()
        )
        cls.sticker.collector = cls.collector.user
        cls.sticker.save()
        cls.sticker.refresh_from_db()
        cls.slot = Slot.objects.filter(absolute_number=cls.sticker.number).first()
        cls.url = reverse("place-sticker", kwargs={"sticker_id": cls.sticker.pk})
        cls.data = {"slot_id": cls.slot.pk}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

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
        other_album = AlbumFactory(
            collector=other_collector.user, collection=self.edition.collection
        )
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


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class DiscoverPrizeViewTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        PromotionFactory()
        collection = CollectionFactory(
            album_template__with_coordinate_images=True, with_prizes_defined=True
        )
        cls.edition = EditionFactory(collection=collection)
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

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

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


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class CreatePagePrizeViewTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        PromotionFactory()
        collection = CollectionFactory(
            album_template__with_coordinate_images=True, with_prizes_defined=True
        )
        coordinate = Coordinate.objects.get(rarity_factor=0.02)
        coordinate.rarity_factor = 1
        coordinate.save()
        edition = EditionFactory(collection=collection)
        cls.user = UserFactory()
        cls.collector = CollectorFactory(user=UserFactory())
        cls.album = AlbumFactory(
            collector=cls.collector.user, collection=edition.collection
        )
        cls.page = Page.objects.get(number=1)
        cls.packs = Pack.objects.all()
        cls.url = reverse("create-page-prize", kwargs={"page_id": cls.page.id})

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_page_prize_succesful_creation(self):
        for pack in self.packs:
            pack.open(self.album.collector)

        stickers = Sticker.objects.filter(
            on_the_board=True, coordinate__absolute_number__lte=6
        )
        for slot in self.page.slots.all():
            sticker = stickers.get(coordinate__absolute_number=slot.absolute_number)
            slot.place_sticker(sticker)

        expected_data = {
            "id": 1,
            "page": self.page.id,
            "prize": {
                "id": self.page.prize.id,
                "collection": self.album.collection.id,
                "collection_name": self.album.collection.album_template.name,
                "page": self.page.number,
                "description": self.page.prize.description,
            },
            "claimed_by": None,
            "claimed_date": None,
            "status": 1,
            "status_display": "No reclamado",
        }

        self.client.force_authenticate(user=self.collector.user)
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, expected_data)

    def test_collector_cannot_create_someone_else_page_prize(self):
        for pack in self.packs:
            pack.open(self.album.collector)

        stickers = Sticker.objects.filter(
            on_the_board=True, coordinate__absolute_number__lte=6
        )
        for slot in self.page.slots.all():
            sticker = stickers.get(coordinate__absolute_number=slot.absolute_number)
            slot.place_sticker(sticker)

        collector = CollectorFactory(user=UserFactory())
        self.client.force_authenticate(user=collector.user)
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "Solo puedes crear premios de tus propias colecciones",
        )

    def test_user_cannot_create_page_prize(self):
        for pack in self.packs:
            pack.open(self.album.collector)

        stickers = Sticker.objects.filter(
            on_the_board=True, coordinate__absolute_number__lte=6
        )
        for slot in self.page.slots.all():
            sticker = stickers.get(coordinate__absolute_number=slot.absolute_number)
            slot.place_sticker(sticker)

        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "Solo los coleccionistas pueden realizar esta acción",
        )

    def test_unauthorized_user_cannot_create_page_prize(self):
        for pack in self.packs:
            pack.open(self.album.collector)

        stickers = Sticker.objects.filter(
            on_the_board=True, coordinate__absolute_number__lte=6
        )
        for slot in self.page.slots.all():
            sticker = stickers.get(coordinate__absolute_number=slot.absolute_number)
            slot.place_sticker(sticker)

        self.client.logout()
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Debe iniciar sesión para realizar esta acción"
        )

    def test_cannot_create_page_prize_twice(self):
        for pack in self.packs:
            pack.open(self.album.collector)

        stickers = Sticker.objects.filter(
            on_the_board=True, coordinate__absolute_number__lte=6
        )
        for slot in self.page.slots.all():
            sticker = stickers.get(coordinate__absolute_number=slot.absolute_number)
            slot.place_sticker(sticker)

        self.client.force_authenticate(user=self.collector.user)
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response2 = self.client.post(self.url)

        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response2.data["detail"], "Esta página ya tiene un premio asignado"
        )

    def test_cannot_create_page_prize_for_an_empty_page(self):

        self.client.force_authenticate(user=self.collector.user)
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["page"][0], "Cannot create a prize for an incomplete page."
        )

    def test_method_not_allowed(self):
        self.client.force_authenticate(user=self.collector.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data["detail"], 'Método "GET" no permitido.')


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class RescuePoolViewTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.user = UserFactory()
        cls.collector = CollectorFactory(user=UserFactory())

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.promotion = PromotionFactory()
        self.collection = collection = CollectionFactory(
            album_template__with_coordinate_images=True, with_prizes_defined=True
        )
        EditionFactory(collection=collection)
        self.album = AlbumFactory(collector=self.collector.user, collection=collection)
        self.url = reverse("rescue-pool", kwargs={"collection_id": collection.id})
        packs = Pack.objects.all()

        for pack in packs:
            pack.open(self.album.collector)

        self.collector.rescue_tickets = 3
        self.collector.save()
        self.collector.refresh_from_db()
        self.client.force_authenticate(user=self.collector.user)

    def test_collector_can_access_rescue_pool_view(self):
        collector = CollectorFactory(user=UserFactory())
        collector.rescue_tickets = 3
        collector.save()
        collector.refresh_from_db()
        response = self.client.get(self.url)

        self.client.force_authenticate(user=collector.user)

        response2 = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertQuerySetEqual(response.data, [])
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response2.data), 16)

    def test_not_collector_cannot_access_rescue_pool_view(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "Solo los coleccionistas pueden realizar esta acción",
        )

    def test_unauthenticated_user_cannot_access_rescue_pool_view(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Debe iniciar sesión para realizar esta acción"
        )

    def test_collector_with_not_enough_tickets_cannot_access_rescue_pool_view(self):
        self.collector.rescue_tickets = 0
        self.collector.save()
        self.collector.refresh_from_db()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            str(response.data["detail"]),
            "Necesitas 3 tickets para acceder al pool de rescate. Por cada sobre comprado, obtienes 1 ticket.",
        )

    def test_method_not_allowed(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data["detail"], 'Método "POST" no permitido.')

    def test_response_without_promotion(self):
        Promotion.objects.all().delete()
        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            "No hay ninguna promoción en curso, no es posible la consulta.",
        )

    def test_invalid_collection_id(self):
        # Test with a non-existent collection ID
        invalid_url = reverse("rescue-pool", kwargs={"collection_id": 9999})
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data["detail"],
            "La colección especificada no existe o no pertenece a la promoción actual.",
        )

    def test_collection_from_different_promotion(self):
        other_promotion = PromotionFactory(past=True)

        with patch("promotions.models.Promotion.objects.get_current") as mock:
            mock.return_value = other_promotion
            other_collection = CollectionFactory(album_template__name="Angela")

        self.collector.rescue_tickets = 3
        self.collector.save()
        self.collector.refresh_from_db()
        other_url = reverse(
            "rescue-pool", kwargs={"collection_id": other_collection.id}
        )

        response = self.client.get(other_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data["detail"],
            "La colección especificada no existe o no pertenece a la promoción actual.",
        )

    def test_no_collection_id_provided(self):
        factory = APIRequestFactory()
        request = factory.get("/api/stickers/rescue-pool/")
        view = RescuePoolView.as_view()

        force_authenticate(request, user=self.collector.user)
        response = view(request, **{})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data[0], "Se requiere un ID de colección.")
