from unittest import skip
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from django.conf import settings

from authentication.test.factories import UserFactory
from ..models import RegionalManager, LocalManager

from .factories import RegionalManagerFactory

User = get_user_model()


class CustomTokenObtainPairViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test_user@example.com", password="testpassword")
        self.url = reverse("jwt_create")

    def test_post_creates_cookies(self):
        data = {
            "email": "test_user@example.com",
            "password": "testpassword"
        }
        self.client.login(username="test_user@example.com",
                          password="testpassword")

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.cookies)
        self.assertEqual(
            response.cookies["access"].value, response.data["access"])
        self.assertIn("refresh", response.cookies)
        self.assertEqual(
            response.cookies["refresh"].value, response.data["refresh"])
        self.assertEqual(
            response.cookies["access"]["max-age"], settings.AUTH_COOKIE_ACCESS_MAX_AGE)
        self.assertEqual(
            response.cookies["access"]["path"], settings.AUTH_COOKIE_PATH)
        self.assertEqual(
            response.cookies["access"]["httponly"], settings.AUTH_COOKIE_HTTP_ONLY)
        self.assertEqual(
            response.cookies["access"]["samesite"], settings.AUTH_COOKIE_SAMESITE)
        self.assertEqual(
            response.cookies["refresh"]["path"], settings.AUTH_COOKIE_PATH)
        self.assertEqual(
            response.cookies["refresh"]["httponly"], settings.AUTH_COOKIE_HTTP_ONLY)
        self.assertEqual(
            response.cookies["refresh"]["samesite"], settings.AUTH_COOKIE_SAMESITE)


class CustomTokenRefreshViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test_user@example.com", password="testpassword")
        self.jwt_create_url = reverse("jwt_create")
        self.url = reverse("jwt_refresh")

    def test_post_creates_cookies(self):
        data = {
            "email": "test_user@example.com",
            "password": "testpassword"
        }

        self.client.login(email="test_user@example.com",
                          password="testpassword")
        self.client.post(self.jwt_create_url, data, format="json")
        data = {}
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.cookies)
        self.assertEqual(
            response.cookies["access"].value, response.data["access"])
        self.assertEqual(
            response.cookies["access"]["max-age"], settings.AUTH_COOKIE_ACCESS_MAX_AGE)
        self.assertEqual(
            response.cookies["access"]["path"], settings.AUTH_COOKIE_PATH)
        self.assertEqual(
            response.cookies["access"]["httponly"], settings.AUTH_COOKIE_HTTP_ONLY)
        self.assertEqual(
            response.cookies["access"]["samesite"], settings.AUTH_COOKIE_SAMESITE)


class CustomTokenVerifyViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test_user@example.com", password="testpassword")
        self.jwt_create_url = reverse("jwt_create")
        self.jwt_verify_url = reverse("jwt_verify")

    def test_post_creates_cookies(self):
        data = {
            "email": "test_user@example.com",
            "password": "testpassword"
        }

        self.client.login(username="test_user@example.com",
                          password="testpassword")
        self.client.post(
            self.jwt_create_url, data, format="json")
        data = {}
        response = self.client.post(
            self.jwt_verify_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class LogoutViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test_user@example.com", password="testpassword")
        self.create_url = reverse("jwt_create")
        self.logout_url = reverse("logout")

    def test_post_delete_cookies(self):
        data = {
            "email": "test_user@example.com",
            "password": "testpassword"
        }
        self.client.login(email="test_user@example.com",
                          password="testpassword")
        response = self.client.post(self.create_url, data, format="json")

        self.assertIn("access", response.cookies)
        self.assertIn("refresh", response.cookies)

        logout_response = self.client.post(self.logout_url)

        self.assertEqual(logout_response.status_code,
                         status.HTTP_204_NO_CONTENT)
        self.assertEqual(logout_response.cookies['access'].value, '')
        self.assertEqual(logout_response.cookies['refresh'].value, '')
        self.assertEqual(logout_response.cookies['access']['max-age'], 0)
        self.assertEqual(logout_response.cookies['refresh']['max-age'], 0)


# @skip("this")
class RegionalManagerViewSetTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_superuser(
            email="superuser@example.com", password="superpassword")
        self.client.force_authenticate(user=self.user)
        self.list_url = reverse('regional-manager-profile-list')
        self.count_url = reverse('regional-manager-profile-count')

    def test_get_regional_managers(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_regional_manager(self):
        data = {
            'first_name': 'Test',
            'middle_name': "Manager",
            'last_name': 'Parra',
            'second_last_name': 'García',
            'gender': 'F',
            'birthdate': '2000-05-01',
            'email': 'testmanager@example.com'
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RegionalManager.objects.count(), 1)
        self.assertIsNone(RegionalManager.objects.get().user)
        self.assertEqual(
            RegionalManager.objects.get().first_name, 'Test')
        self.assertEqual(
            RegionalManager.objects.get().middle_name, 'Manager')
        self.assertEqual(
            RegionalManager.objects.get().last_name, 'Parra')
        self.assertEqual(
            RegionalManager.objects.get().second_last_name, 'García')
        self.assertEqual(
            RegionalManager.objects.get().gender, 'F')
        self.assertEqual(
            str(RegionalManager.objects.get().birthdate), '2000-05-01')
        self.assertEqual(
            RegionalManager.objects.get().email, 'testmanager@example.com')

    def test_count_regional_managers(self):
        RegionalManagerFactory()
        RegionalManagerFactory()
        response = self.client.get(self.count_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total'], 2)


class LocalManagerViewSetTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.superuser = UserFactory(is_superuser=True)
        self.user = UserFactory()
        self.regional_manager = RegionalManagerFactory(user=self.user)
        self.client.force_authenticate(user=self.superuser)
        self.list_url = reverse('local-manager-profile-list')
        self.count_url = reverse('local-manager-profile-count')

    def test_get_local_managers(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_local_manager(self):
        data = {
            'first_name': 'Local',
            'last_name': 'Parra',
            'gender': 'F',
            'email': 'localmanager@example.com'
        }
        response = self.client.post(self.list_url, data, format='json')
        manager = LocalManager.objects.get(first_name='Local')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(LocalManager.objects.count(), 1)
        self.assertIsNone(manager.user)
        self.assertEqual(manager.first_name, 'Local')
        self.assertEqual(manager.last_name, 'Parra')
        self.assertEqual(manager.gender, 'F')
        self.assertEqual(manager.email, 'localmanager@example.com')

    # def test_count_regional_managers(self):
    #     RegionalManagerFactory()
    #     RegionalManagerFactory()
    #     response = self.client.get(self.count_url)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(response.data['total'], 2)
