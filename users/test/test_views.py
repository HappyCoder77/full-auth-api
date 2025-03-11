from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings
from rest_framework.test import APIClient, APITestCase, APIRequestFactory
from rest_framework import status
from rest_framework import status

from collection_manager.test.factories import ThemeFactory, CollectionFactory
from promotions.test.factories import PromotionFactory
from promotions.models import Promotion
from editions.test.factories import EditionFactory
from authentication.test.factories import UserFactory
from ..models import RegionalManager, LocalManager, Sponsor, Dealer, Collector
from .factories import (
    RegionalManagerFactory,
    LocalManagerFactory,
    SponsorFactory,
    DealerFactory,
    CollectorFactory,
)
from ..permissions import DetailedPermissionDenied
from ..views import CollectorViewSet
from commerce.test.factories import OrderFactory
from commerce.models import Order


User = get_user_model()


class RegionalManagerViewSetTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.list_url = reverse("regional-manager-list")
        self.count_url = reverse("regional-manager-count")

    def test_get_regional_managers(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_regional_managers_unauthorized(self):
        self.client.logout()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(len(response.data), 1)

    def test_get_regional_managers_forbidden(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(len(response.data), 1)

    def test_get_list_regional_managers(self):
        RegionalManagerFactory(created_by=self.user)
        RegionalManagerFactory(created_by=self.user)
        RegionalManagerFactory(created_by=self.user)

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_get_list_regional_managers_unauthorized(self):
        self.client.logout()
        RegionalManagerFactory(created_by=self.user)
        RegionalManagerFactory(created_by=self.user)
        RegionalManagerFactory(created_by=self.user)

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(len(response.data), 1)

    def test_get_list_regional_managers_forbidden(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)
        RegionalManagerFactory(created_by=self.user)
        RegionalManagerFactory(created_by=self.user)
        RegionalManagerFactory(created_by=self.user)

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(len(response.data), 1)

    def test_create_regional_manager(self):
        data = {
            "first_name": "Test",
            "middle_name": "Manager",
            "last_name": "Parra",
            "second_last_name": "García",
            "gender": "F",
            "birthdate": "2000-05-01",
            "email": "testmanager@example.com",
        }
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RegionalManager.objects.count(), 1)
        self.assertIsNone(response.data.get("user"))
        self.assertEqual(response.data["first_name"], "Test")
        self.assertEqual(response.data["middle_name"], "Manager")
        self.assertEqual(response.data["last_name"], "Parra")
        self.assertEqual(response.data["second_last_name"], "García")
        self.assertEqual(response.data["gender"], "F")
        self.assertEqual(str(response.data["birthdate"]), "2000-05-01")
        self.assertEqual(response.data["email"], "testmanager@example.com")
        self.assertEqual(response.data["created_by"], self.user.id)

    def test_create_regional_manager_unauthorized(self):
        self.client.logout()
        data = {
            "first_name": "Test",
            "middle_name": "Manager",
            "last_name": "Parra",
            "second_last_name": "García",
            "gender": "F",
            "birthdate": "2000-05-01",
            "email": "testmanager@example.com",
        }
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(RegionalManager.objects.count(), 0)

    def test_create_regional_manager_forbidden(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)
        data = {
            "first_name": "Test",
            "middle_name": "Manager",
            "last_name": "Parra",
            "second_last_name": "García",
            "gender": "F",
            "birthdate": "2000-05-01",
            "email": "testmanager@example.com",
        }
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(RegionalManager.objects.count(), 0)

    def test_count_regional_managers(self):
        RegionalManagerFactory()
        RegionalManagerFactory()
        response = self.client.get(self.count_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total"], 2)

    def test_count_regional_managers_unauthorized(self):
        self.client.logout()
        RegionalManagerFactory()
        RegionalManagerFactory()
        response = self.client.get(self.count_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(len(response.data), 1)

    def test_count_regional_managers_forbidden(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)
        RegionalManagerFactory()
        RegionalManagerFactory()
        response = self.client.get(self.count_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(len(response.data), 1)


class LocalManagerViewSetTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.superuser = UserFactory(is_superuser=True)
        self.user = UserFactory()
        self.regional_manager = RegionalManagerFactory(user=self.user)
        self.client.force_authenticate(user=self.regional_manager.user)
        self.list_url = reverse("local-manager-list")
        self.count_url = reverse("local-manager-count")

    def test_get_local_managers(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(LocalManager.objects.count(), 0)

    def test_get_local_managers_with_superuser(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(LocalManager.objects.count(), 0)

    def test_get_local_managers_unauthorized(self):
        self.client.logout()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(len(response.data), 1)

    def test_get_local_managers_forbidden(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(len(response.data), 1)

    def test_create_local_manager(self):
        data = {
            "first_name": "Local",
            "last_name": "Parra",
            "gender": "F",
            "email": "localmanager@example.com",
        }
        response = self.client.post(self.list_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(LocalManager.objects.count(), 1)
        self.assertIsNone(response.data.get("user"))
        self.assertEqual(response.data.get("first_name"), "Local")
        self.assertEqual(response.data.get("last_name"), "Parra")
        self.assertEqual(response.data.get("gender"), "F")
        self.assertEqual(response.data.get("email"), "localmanager@example.com")
        self.assertEqual(response.data.get("created_by"), self.regional_manager.user.id)

    def test_create_local_manager_with_superuser(self):
        self.client.force_authenticate(user=self.superuser)
        data = {
            "first_name": "Local",
            "last_name": "Parra",
            "gender": "F",
            "email": "localmanager@example.com",
        }
        response = self.client.post(self.list_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(LocalManager.objects.count(), 1)
        self.assertIsNone(response.data.get("user"))
        self.assertEqual(response.data.get("created_by"), self.superuser.id)

    def test_create_local_manager_unauthorized(self):
        self.client.logout()
        data = {
            "first_name": "Local",
            "last_name": "Parra",
            "gender": "F",
            "email": "localmanager@example.com",
        }
        response = self.client.post(self.list_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(len(response.data), 1)

    def test_create_local_manager_forbidden(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)
        data = {
            "first_name": "Local",
            "last_name": "Parra",
            "gender": "F",
            "email": "localmanager@example.com",
        }
        response = self.client.post(self.list_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(LocalManager.objects.count(), 0)

    def test_count_with_regional_manager(self):
        LocalManagerFactory(created_by=self.regional_manager.user)
        LocalManagerFactory(created_by=self.regional_manager.user)
        LocalManagerFactory(created_by=self.superuser)
        response = self.client.get(self.count_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total"], 2)

    def test_count_with_superuser(self):
        self.client.force_authenticate(user=self.superuser)
        LocalManagerFactory(created_by=self.superuser)
        LocalManagerFactory(created_by=self.superuser)
        LocalManagerFactory(created_by=self.regional_manager.user)
        response = self.client.get(self.count_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total"], 3)

    def test_count_unauthorized(self):
        self.client.logout()
        LocalManagerFactory(created_by=self.superuser)
        LocalManagerFactory(created_by=self.superuser)
        LocalManagerFactory(created_by=self.regional_manager.user)

        response = self.client.get(self.count_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_count_forbidden(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)
        LocalManagerFactory(created_by=self.superuser)
        LocalManagerFactory(created_by=self.superuser)
        LocalManagerFactory(created_by=self.regional_manager.user)

        response = self.client.get(self.count_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_with_regional_manager(self):
        LocalManagerFactory(created_by=self.regional_manager.user)
        LocalManagerFactory(created_by=self.regional_manager.user)
        LocalManagerFactory(created_by=self.superuser)
        LocalManagerFactory(created_by=self.superuser)

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_with_superuser(self):
        self.client.force_authenticate(user=self.superuser)
        LocalManagerFactory(created_by=self.regional_manager.user)
        LocalManagerFactory(created_by=self.regional_manager.user)
        LocalManagerFactory(created_by=self.superuser)
        LocalManagerFactory(created_by=self.superuser)
        LocalManagerFactory(created_by=self.superuser)

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)

    def test_list_unauthorized(self):
        self.client.logout()
        LocalManagerFactory(created_by=self.regional_manager.user)
        LocalManagerFactory(created_by=self.regional_manager.user)
        LocalManagerFactory(created_by=self.superuser)
        LocalManagerFactory(created_by=self.superuser)
        LocalManagerFactory(created_by=self.superuser)

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(len(response.data), 1)

    def test_list_forbidden(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)
        LocalManagerFactory(created_by=self.regional_manager.user)
        LocalManagerFactory(created_by=self.regional_manager.user)
        LocalManagerFactory(created_by=self.superuser)
        LocalManagerFactory(created_by=self.superuser)
        LocalManagerFactory(created_by=self.superuser)

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(len(response.data), 1)


class SponsorViewSetTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.superuser = UserFactory(is_superuser=True)
        self.user = UserFactory()
        self.localmanager = LocalManagerFactory(user=self.user)
        self.client.force_authenticate(user=self.localmanager.user)
        self.list_url = reverse("sponsor-list")
        self.count_url = reverse("sponsor-count")

    def test_get_sponsors(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Sponsor.objects.count(), 0)

    def test_get_sponsors_with_superuser(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Sponsor.objects.count(), 0)

    def test_get_sponsors_unauthorized(self):
        self.client.logout()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(len(response.data), 1)

    def test_get_sponsors_forbidden(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(len(response.data), 1)

    def test_create_local_manager(self):
        data = {
            "first_name": "Sponsor",
            "last_name": "Parra",
            "gender": "F",
            "email": "localmanager@example.com",
        }
        response = self.client.post(self.list_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Sponsor.objects.count(), 1)
        self.assertIsNone(response.data.get("user"))
        self.assertEqual(response.data.get("first_name"), "Sponsor")
        self.assertEqual(response.data.get("last_name"), "Parra")
        self.assertEqual(response.data.get("gender"), "F")
        self.assertEqual(response.data.get("email"), "localmanager@example.com")
        self.assertEqual(response.data.get("created_by"), self.localmanager.user.id)

    def test_create_local_manager_with_superuser(self):
        self.client.force_authenticate(user=self.superuser)
        data = {
            "first_name": "Sponsor",
            "last_name": "Parra",
            "gender": "F",
            "email": "localmanager@example.com",
        }
        response = self.client.post(self.list_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Sponsor.objects.count(), 1)
        self.assertIsNone(response.data.get("user"))
        self.assertEqual(response.data.get("created_by"), self.superuser.id)

    def test_create_local_manager_unauthorized(self):
        self.client.logout()
        data = {
            "first_name": "Sponsor",
            "last_name": "Parra",
            "gender": "F",
            "email": "localmanager@example.com",
        }
        response = self.client.post(self.list_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(len(response.data), 1)

    def test_create_local_manager_forbidden(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)
        data = {
            "first_name": "Sponsor",
            "last_name": "Parra",
            "gender": "F",
            "email": "localmanager@example.com",
        }
        response = self.client.post(self.list_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Sponsor.objects.count(), 0)

    def test_count_with_localmanager(self):
        SponsorFactory(created_by=self.localmanager.user)
        SponsorFactory(created_by=self.localmanager.user)
        SponsorFactory(created_by=self.superuser)
        response = self.client.get(self.count_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total"], 2)

    def test_count_with_superuser(self):
        self.client.force_authenticate(user=self.superuser)
        SponsorFactory(created_by=self.superuser)
        SponsorFactory(created_by=self.superuser)
        SponsorFactory(created_by=self.localmanager.user)
        response = self.client.get(self.count_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total"], 3)

    def test_count_unauthorized(self):
        self.client.logout()
        SponsorFactory(created_by=self.superuser)
        SponsorFactory(created_by=self.superuser)
        SponsorFactory(created_by=self.localmanager.user)

        response = self.client.get(self.count_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_count_forbidden(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)
        SponsorFactory(created_by=self.superuser)
        SponsorFactory(created_by=self.superuser)
        SponsorFactory(created_by=self.localmanager.user)

        response = self.client.get(self.count_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_with_sponsor(self):
        SponsorFactory(created_by=self.localmanager.user)
        SponsorFactory(created_by=self.localmanager.user)
        SponsorFactory(created_by=self.superuser)
        SponsorFactory(created_by=self.superuser)

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_with_superuser(self):
        self.client.force_authenticate(user=self.superuser)
        SponsorFactory(created_by=self.localmanager.user)
        SponsorFactory(created_by=self.localmanager.user)
        SponsorFactory(created_by=self.superuser)
        SponsorFactory(created_by=self.superuser)
        SponsorFactory(created_by=self.superuser)

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)

    def test_list_unauthorized(self):
        self.client.logout()
        SponsorFactory(created_by=self.localmanager.user)
        SponsorFactory(created_by=self.localmanager.user)
        SponsorFactory(created_by=self.superuser)
        SponsorFactory(created_by=self.superuser)
        SponsorFactory(created_by=self.superuser)

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(len(response.data), 1)

    def test_list_forbidden(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)
        SponsorFactory(created_by=self.localmanager.user)
        SponsorFactory(created_by=self.localmanager.user)
        SponsorFactory(created_by=self.superuser)
        SponsorFactory(created_by=self.superuser)
        SponsorFactory(created_by=self.superuser)

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(len(response.data), 1)


class DealerViewSetTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.superuser = UserFactory(is_superuser=True)
        self.user = UserFactory()
        self.sponsor = SponsorFactory(user=self.user)
        self.client.force_authenticate(user=self.sponsor.user)
        self.list_url = reverse("dealer-list")
        self.count_url = reverse("dealer-count")

    def test_get_dealers(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Dealer.objects.count(), 0)

    def test_get_dealers_with_superuser(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Dealer.objects.count(), 0)

    def test_get_dealers_unauthorized(self):
        self.client.logout()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(len(response.data), 1)

    def test_get_dealers_forbidden(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(len(response.data), 1)

    def test_create_local_manager(self):
        data = {
            "first_name": "Dealer",
            "last_name": "Parra",
            "gender": "F",
            "email": "localmanager@example.com",
        }
        response = self.client.post(self.list_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Dealer.objects.count(), 1)
        self.assertIsNone(response.data.get("user"))
        self.assertEqual(response.data.get("first_name"), "Dealer")
        self.assertEqual(response.data.get("last_name"), "Parra")
        self.assertEqual(response.data.get("gender"), "F")
        self.assertEqual(response.data.get("email"), "localmanager@example.com")
        self.assertEqual(response.data.get("created_by"), self.sponsor.user.id)

    def test_create_local_manager_with_superuser(self):
        self.client.force_authenticate(user=self.superuser)
        data = {
            "first_name": "Dealer",
            "last_name": "Parra",
            "gender": "F",
            "email": "localmanager@example.com",
        }
        response = self.client.post(self.list_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Dealer.objects.count(), 1)
        self.assertIsNone(response.data.get("user"))
        self.assertEqual(response.data.get("created_by"), self.superuser.id)

    def test_create_local_manager_unauthorized(self):
        self.client.logout()
        data = {
            "first_name": "Dealer",
            "last_name": "Parra",
            "gender": "F",
            "email": "localmanager@example.com",
        }
        response = self.client.post(self.list_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(len(response.data), 1)

    def test_create_local_manager_forbidden(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)
        data = {
            "first_name": "Dealer",
            "last_name": "Parra",
            "gender": "F",
            "email": "localmanager@example.com",
        }
        response = self.client.post(self.list_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Dealer.objects.count(), 0)

    def test_count_with_localmanager(self):
        DealerFactory(created_by=self.sponsor.user)
        DealerFactory(created_by=self.sponsor.user)
        DealerFactory(created_by=self.superuser)
        response = self.client.get(self.count_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total"], 2)

    def test_count_with_superuser(self):
        self.client.force_authenticate(user=self.superuser)
        DealerFactory(created_by=self.superuser)
        DealerFactory(created_by=self.superuser)
        DealerFactory(created_by=self.sponsor.user)
        response = self.client.get(self.count_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total"], 3)

    def test_count_unauthorized(self):
        self.client.logout()
        DealerFactory(created_by=self.superuser)
        DealerFactory(created_by=self.superuser)
        DealerFactory(created_by=self.sponsor.user)

        response = self.client.get(self.count_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_count_forbidden(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)
        DealerFactory(created_by=self.superuser)
        DealerFactory(created_by=self.superuser)
        DealerFactory(created_by=self.sponsor.user)

        response = self.client.get(self.count_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_with_sponsor(self):
        DealerFactory(created_by=self.sponsor.user)
        DealerFactory(created_by=self.sponsor.user)
        DealerFactory(created_by=self.superuser)
        DealerFactory(created_by=self.superuser)

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_with_superuser(self):
        self.client.force_authenticate(user=self.superuser)
        DealerFactory(created_by=self.sponsor.user)
        DealerFactory(created_by=self.sponsor.user)
        DealerFactory(created_by=self.superuser)
        DealerFactory(created_by=self.superuser)
        DealerFactory(created_by=self.superuser)

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)

    def test_list_unauthorized(self):
        self.client.logout()
        DealerFactory(created_by=self.sponsor.user)
        DealerFactory(created_by=self.sponsor.user)
        DealerFactory(created_by=self.superuser)
        DealerFactory(created_by=self.superuser)
        DealerFactory(created_by=self.superuser)

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(len(response.data), 1)

    def test_list_forbidden(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)
        DealerFactory(created_by=self.sponsor.user)
        DealerFactory(created_by=self.sponsor.user)
        DealerFactory(created_by=self.superuser)
        DealerFactory(created_by=self.superuser)
        DealerFactory(created_by=self.superuser)

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(len(response.data), 1)


class CollectorViewSetTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.superuser = UserFactory(is_superuser=True)
        self.user = UserFactory()
        self.collector = CollectorFactory(user=self.user, email=self.user.email)
        self.client.force_authenticate(user=self.collector.user)
        self.list_url = reverse("collector-list")
        self.me_url = reverse("collector-me")
        self.detail_url = reverse("collector-detail", kwargs={"pk": self.collector.pk})
        self.count_url = reverse("collector-count")

    def test_get_collector_detail(self):
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 13)

    def test_get_collector_detail_with_superuser(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 13)

    def test_get_collector_detail_unauthorized(self):
        self.client.logout()
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(len(response.data), 1)

    def test_get_collector_detail_not_owner(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"], "Solo puedes acceder a tu propio perfil."
        )

    def test_get_collector_me(self):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], 1)
        self.assertEqual(response.data["first_name"], self.collector.first_name)
        self.assertEqual(response.data["middle_name"], self.collector.middle_name)
        self.assertEqual(response.data["last_name"], self.collector.last_name)
        self.assertEqual(
            response.data["second_last_name"], self.collector.second_last_name
        )
        self.assertEqual(response.data["gender"], self.collector.gender)
        self.assertEqual(response.data["birthdate"], self.collector.birthdate)
        self.assertEqual(response.data["email"], self.user.email)

    def test_get_collector_me_forbidden(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(self.me_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(len(response.data), 1)

    def test_get_collector_me_unauthorized(self):
        self.client.logout()
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(len(response.data), 1)

    def test_create_collector(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)
        data = {
            "first_name": "Collector",
            "last_name": "Parra",
            "gender": "F",
        }

        response = self.client.post(self.list_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Collector.objects.count(), 2)
        self.assertEqual(response.data.get("first_name"), "Collector")
        self.assertEqual(response.data.get("last_name"), "Parra")
        self.assertEqual(response.data.get("gender"), "F")
        self.assertEqual(response.data.get("email"), user.email)

    def test_create_collector_forbidden(self):
        user = UserFactory()
        manager = RegionalManagerFactory(user=user)
        self.client.force_authenticate(user=manager.user)
        data = {
            "first_name": "Collector",
            "last_name": "Parra",
            "gender": "F",
            "email": "collector@example.com",
        }
        response = self.client.post(self.list_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_collector_forbidden_superuser(self):
        self.client.force_authenticate(user=self.superuser)
        data = {
            "first_name": "Collector",
            "last_name": "Parra",
            "gender": "F",
            "email": "collector@example.com",
        }
        response = self.client.post(self.list_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_collector_unauthorized(self):
        self.client.logout()
        data = {
            "first_name": "Collector",
            "last_name": "Parra",
            "gender": "F",
            "email": "collector@example.com",
        }

        response = self.client.post(self.list_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_count_collector(self):
        self.client.force_authenticate(user=self.superuser)
        user = UserFactory()
        user2 = UserFactory()
        user3 = UserFactory()
        CollectorFactory(user=user)
        CollectorFactory(user=user2)
        CollectorFactory(user=user3)
        response = self.client.get(self.count_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total"], 4)

    def test_count_collector_forbidden(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)
        response = self.client.get(self.count_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_count_collector_unauthorized(self):
        self.client.logout()
        response = self.client.get(self.count_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_collector(self):
        self.client.force_authenticate(user=self.superuser)
        user = UserFactory()
        user2 = UserFactory()
        user3 = UserFactory()
        CollectorFactory(user=user)
        CollectorFactory(user=user2)
        CollectorFactory(user=user3)

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    def test_list_collector_forbidden(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_collector_unauthorized(self):
        self.client.logout()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_collector(self):
        data = {
            "first_name": "UpdatedName",
            "last_name": "UpdatedLastName",
            "gender": "M",
        }
        response = self.client.patch(self.detail_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["first_name"], "UpdatedName")
        self.assertEqual(response.data["last_name"], "UpdatedLastName")
        self.assertEqual(response.data["gender"], "M")

    def test_update_collector_forbidden(self):
        self.client.force_authenticate(user=self.superuser)
        data = {
            "first_name": "UpdatedName",
            "last_name": "UpdatedLastName",
            "gender": "M",
        }
        response = self.client.put(self.detail_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_collector_unauthorized(self):
        self.client.logout()
        data = {
            "first_name": "UpdatedName",
            "last_name": "UpdatedLastName",
            "gender": "M",
        }
        response = self.client.put(self.detail_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_destroy_collector(self):
        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_superuser_cannot_modify_other_collector(self):
        self.client.force_authenticate(user=self.superuser)
        data = {"first_name": "UpdatedName"}
        response = self.client.patch(self.detail_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "Los superusuarios solo pueden ver perfiles, no modificarlos.",
        )

    def test_cannot_create_second_collector_profile(self):
        data = {
            "first_name": "Collector",
            "last_name": "Parra",
            "gender": "F",
        }

        response = self.client.post(self.list_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"], "Ya tienes un perfil creado. No puedes crear otro."
        )

    def test_get_collector_non_existent(self):
        non_existent_url = reverse("collector-detail", kwargs={"pk": 14567})
        response = self.client.get(non_existent_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("No encontrado.", response.data["detail"])

    def test_handle_exception_detailed_permission_denied(self):
        # Crea una instancia de CollectorViewSet
        view = CollectorViewSet()

        # Configura la solicitud
        factory = APIRequestFactory()
        request = factory.get("/fake-url/")

        # Fuerza la autenticación con un usuario que no tiene permiso
        user = UserFactory()
        self.client.force_authenticate(user=user)

        # Simula una excepción DetailedPermissionDenied
        exception = DetailedPermissionDenied(
            detail="Mensaje de error personalizado",
            status_code=status.HTTP_403_FORBIDDEN,
        )

        # Llama al método handle_exception
        response = view.handle_exception(exception)

        # Verifica que la respuesta sea correcta
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {"detail": "Mensaje de error personalizado"})

    def test_handle_exception_other_exception(self):
        # Crea una instancia de CollectorViewSet
        view = CollectorViewSet()

        # Simula otra excepción
        exception = ValueError("Otro tipo de error")

        # Llama al método handle_exception
        response = view.handle_exception(exception)

        # Verifica que la respuesta sea la predeterminada para otras excepciones
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data, {"detail": "Se produjo un error inesperado."})


class DealerStockAPIViewAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superuser = UserFactory(is_superuser=True)
        dealer_user = UserFactory()
        cls.dealer = DealerFactory(user=dealer_user)
        cls.basic_user = UserFactory()

        with patch("promotions.models.Promotion.objects.get_current") as mock_current:
            cls.past_promotion = PromotionFactory(past=True)
            mock_current.return_value = cls.past_promotion
            theme = ThemeFactory(name="Roblox")
            theme_2 = ThemeFactory(name="Mario")
            collection = CollectionFactory(theme=theme)
            collection_2 = CollectionFactory(theme=theme_2)

            cls.past_edition = EditionFactory(collection=collection)
            cls.past_edition2 = EditionFactory(collection=collection_2)

    def setUp(self):
        self.promotion = PromotionFactory()
        self.edition = EditionFactory()

        self.url = reverse(
            "dealer-edition-stock", kwargs={"collection_id": self.edition.collection.id}
        )

    def test_dealer_can_get_initial_stock(self):
        self.client.force_authenticate(user=self.dealer.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["stock"], 0)

    def test_superuser_cannot_get_stock(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"], "Sólo los detallistas pueden realizar esta acción"
        )

    def test_basic_user_cannot_get_stock(self):
        self.client.force_authenticate(user=self.basic_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"], "Sólo los detallistas pueden realizar esta acción"
        )

    def test_unauthenticated_user_cannot_get_stock(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Debe iniciar sesión para realizar esta accion"
        )

    def test_get_updated_stock_after_order(self):
        OrderFactory(dealer=self.dealer.user, collection=self.edition.collection)
        self.client.force_authenticate(user=self.dealer.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["stock"], 15)

    def test_get_stock_without_current_promotion(self):
        Promotion.objects.all().delete()
        self.client.force_authenticate(user=self.dealer.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["detail"], "No hay ninguna promoción en curso.")

    def test_get_stock_from_past_edition(self):
        with patch("promotions.models.Promotion.objects.get_current") as mock_current:
            promotion = PromotionFactory(past=True)
            mock_current.return_value = promotion
            edition = EditionFactory(collection__theme__name="Angela")
            OrderFactory(dealer=self.dealer.user, collection=edition.collection)

        self.client.force_authenticate(user=self.dealer.user)
        url = reverse(
            "dealer-edition-stock", kwargs={"collection_id": edition.collection.id}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data["detail"],
            "No hay ninguna colección activa con el id suministrado",
        )

    def test_get_stock_with_expired_promotion(self):
        self.promotion.delete()
        OrderFactory(
            dealer=self.dealer.user,
            collection=self.past_edition.collection,
            skip_validation=True,
        )
        OrderFactory(
            dealer=self.dealer.user,
            collection=self.past_edition2.collection,
            skip_validation=True,
        )
        self.client.force_authenticate(user=self.dealer.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Order.objects.all().count(), 2)
        self.assertEqual(
            response.data["detail"],
            "No hay ninguna promoción en curso.",
        )

    def test_method_not_allowed(self):
        self.client.force_authenticate(user=self.dealer.user)
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data["detail"], 'Método "POST" no permitido.')


class CollectorLookupViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.user = UserFactory()
        cls.collector = CollectorFactory(user=cls.user, email=cls.user.email)
        cls.url = reverse("collector-lookup")

    def test_can_lookup_collector_by_email(self):
        self.client.force_authenticate(user=self.collector.user)
        response = self.client.get(f"{self.url}?email={self.collector.email}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.collector.user.id)
        self.assertEqual(response.data["email"], self.collector.email)
        self.assertEqual(response.data["full_name"], self.collector.get_full_name)

    def test_returns_404_for_nonexistent_collector(self):
        self.client.force_authenticate(user=self.collector.user)
        response = self.client.get(f"{self.url}?email=nonexistent@email.com")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data["detail"],
            "No existe un coleccionista con el correo ingresado",
        )

    def test_returns_404_when_email_param_missing(self):
        self.client.force_authenticate(user=self.collector.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data["detail"],
            "No existe un coleccionista con el correo ingresado",
        )

    def test_unauthenticated_user_cannot_lookup_collector_by_email(self):
        response = self.client.get(f"{self.url}?email={self.collector.email}")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"],
            "Las credenciales de autenticación no se proveyeron.",
        )

    def test_method_not_allowed(self):
        self.client.force_authenticate(user=self.collector.user)
        response = self.client.post(f"{self.url}?email={self.collector.email}")

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(
            response.data["detail"],
            'Método "POST" no permitido.',
        )
