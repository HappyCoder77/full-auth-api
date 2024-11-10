from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.conf import settings
from rest_framework.test import APIClient
from rest_framework import status


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
