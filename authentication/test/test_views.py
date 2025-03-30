import time
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.conf import settings
from rest_framework.test import APIClient
from rest_framework import status

from .factories import UserFactory


User = get_user_model()


class CustomTokenObtainPairViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory(
            email="test_user@example.com", password="testpassword", active=True
        )
        self.url = reverse("jwt_create")

    def test_post_creates_cookies(self):
        data = {"email": self.user.email, "password": "testpassword"}

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.cookies)
        self.assertEqual(response.cookies["access"].value, response.data["access"])
        self.assertIn("refresh", response.cookies)
        self.assertEqual(response.cookies["refresh"].value, response.data["refresh"])
        self.assertEqual(
            response.cookies["access"]["max-age"], settings.AUTH_COOKIE_ACCESS_MAX_AGE
        )
        self.assertEqual(response.cookies["access"]["path"], settings.AUTH_COOKIE_PATH)
        self.assertEqual(
            response.cookies["access"]["httponly"], settings.AUTH_COOKIE_HTTP_ONLY
        )
        self.assertEqual(
            response.cookies["access"]["samesite"], settings.AUTH_COOKIE_SAMESITE
        )
        self.assertEqual(response.cookies["refresh"]["path"], settings.AUTH_COOKIE_PATH)
        self.assertEqual(
            response.cookies["refresh"]["httponly"], settings.AUTH_COOKIE_HTTP_ONLY
        )
        self.assertEqual(
            response.cookies["refresh"]["samesite"], settings.AUTH_COOKIE_SAMESITE
        )


class CustomTokenRefreshViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory(email="test_user@example.com", password="testpassword")
        self.jwt_create_url = reverse("jwt_create")
        self.url = reverse("jwt_refresh")

    def test_post_creates_cookies(self):
        data = {"email": "test_user@example.com", "password": "testpassword"}

        self.client.post(self.jwt_create_url, data, format="json")
        data = {}
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.cookies)
        self.assertEqual(response.cookies["access"].value, response.data["access"])
        self.assertEqual(
            response.cookies["access"]["max-age"], settings.AUTH_COOKIE_ACCESS_MAX_AGE
        )
        self.assertEqual(response.cookies["access"]["path"], settings.AUTH_COOKIE_PATH)
        self.assertEqual(
            response.cookies["access"]["httponly"], settings.AUTH_COOKIE_HTTP_ONLY
        )
        self.assertEqual(
            response.cookies["access"]["samesite"], settings.AUTH_COOKIE_SAMESITE
        )


class CustomTokenVerifyViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory(email="test_user@example.com", password="testpassword")
        self.jwt_create_url = reverse("jwt_create")
        self.jwt_verify_url = reverse("jwt_verify")

    def test_post_creates_cookies(self):
        data = {"email": "test_user@example.com", "password": "testpassword"}

        self.client.post(self.jwt_create_url, data, format="json")
        data = {}
        response = self.client.post(self.jwt_verify_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class LogoutViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory(email="test_user@example.com", password="testpassword")
        self.create_url = reverse("jwt_create")
        self.logout_url = reverse("logout")

    def test_post_delete_cookies(self):
        data = {"email": "test_user@example.com", "password": "testpassword"}

        response = self.client.post(self.create_url, data, format="json")

        self.assertIn("access", response.cookies)
        self.assertIn("refresh", response.cookies)

        logout_response = self.client.post(self.logout_url)

        self.assertEqual(logout_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(logout_response.cookies["access"].value, "")
        self.assertEqual(logout_response.cookies["refresh"].value, "")
        self.assertEqual(logout_response.cookies["access"]["max-age"], 0)
        self.assertEqual(logout_response.cookies["refresh"]["max-age"], 0)


class CheckEmailActivationViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.url = reverse("check_email_activation")
        cls.active_user = UserFactory()
        cls.inactive_user = UserFactory(is_active=False)

    def test_missing_email_returns_error(self):
        """Test that missing email parameter returns a 400 error"""
        with patch("time.sleep"):  # Mock sleep to speed up tests
            response = self.client.post(self.url, {}, format="json")

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data, {"error": "Email is required"})

    def test_nonexistent_email_returns_generic_success(self):
        """Test that non-existent email returns generic success response"""
        with patch("time.sleep"):
            response = self.client.post(
                self.url, {"email": "nonexistent@example.com"}, format="json"
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(
                response.data,
                {
                    "status": "success",
                    "message": "If this account exists and is not activated, please check your email for activation instructions.",
                },
            )

            self.assertNotIn("pending_activation_email", self.client.session)

    def test_active_user_email_returns_generic_success(self):
        """Test that active user email returns generic success response"""
        with patch("time.sleep"):
            response = self.client.post(
                self.url, {"email": self.active_user.email}, format="json"
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(
                response.data,
                {
                    "status": "success",
                    "message": "If this account exists and is not activated, please check your email for activation instructions.",
                },
            )

            self.assertNotIn("pending_activation_email", self.client.session)

    def test_inactive_user_email_stores_in_session(self):
        """Test that inactive user email is stored in session"""
        with patch("time.sleep"):
            response = self.client.post(
                self.url, {"email": self.inactive_user.email}, format="json"
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(
                response.data,
                {
                    "status": "success",
                    "message": "If this account exists and is not activated, please check your email for activation instructions.",
                },
            )

            self.assertEqual(
                self.client.session.get("pending_activation_email"),
                self.inactive_user.email,
            )

    def test_minimum_response_time_enforced(self):
        """Test that the view enforces a minimum response time"""
        with patch("time.sleep") as mock_sleep:
            # Test with fast execution (should trigger sleep)
            with patch(
                "time.time", side_effect=[0, 0.1]
            ):  # Start time and elapsed time
                self.client.post(self.url, {"email": "test@example.com"}, format="json")
                # Verify sleep was called with appropriate value
                self.assertTrue(mock_sleep.called)
                sleep_time = mock_sleep.call_args[0][0]
                self.assertGreaterEqual(sleep_time, 0.1)  # At least 0.1s

    def test_response_structure_consistency(self):
        """Test that response structure is consistent for all valid requests"""
        expected_response = {
            "status": "success",
            "message": "If this account exists and is not activated, please check your email for activation instructions.",
        }

        with patch("time.sleep"):
            # Test with non-existent email
            response1 = self.client.post(
                self.url, {"email": "nonexistent@example.com"}, format="json"
            )

            # Test with active user
            response2 = self.client.post(
                self.url, {"email": self.active_user.email}, format="json"
            )

            # Test with inactive user
            response3 = self.client.post(
                self.url, {"email": self.inactive_user.email}, format="json"
            )

            self.assertEqual(response1.data, expected_response)
            self.assertEqual(response2.data, expected_response)
            self.assertEqual(response3.data, expected_response)
            self.assertEqual(response1.status_code, status.HTTP_200_OK)
            self.assertEqual(response2.status_code, status.HTTP_200_OK)
            self.assertEqual(response3.status_code, status.HTTP_200_OK)

    def test_timing_attack_protection(self):
        """Test that response times are similar regardless of user existence"""
        # This test measures actual execution times to verify timing consistency

        # We'll run multiple requests to each endpoint to account for system variations
        test_runs = 3
        nonexistent_times = []
        active_times = []
        inactive_times = []

        for _ in range(test_runs):
            # Measure time for non-existent user
            start = time.time()
            self.client.post(
                self.url, {"email": "nonexistent@example.com"}, format="json"
            )
            nonexistent_times.append(time.time() - start)

            # Measure time for active user
            start = time.time()
            self.client.post(self.url, {"email": self.active_user.email}, format="json")
            active_times.append(time.time() - start)

            # Measure time for inactive user
            start = time.time()
            self.client.post(
                self.url, {"email": self.inactive_user.email}, format="json"
            )
            inactive_times.append(time.time() - start)

        # Calculate average times
        avg_nonexistent = sum(nonexistent_times) / len(nonexistent_times)
        avg_active = sum(active_times) / len(active_times)
        avg_inactive = sum(inactive_times) / len(inactive_times)

        # All response times should be at least the minimum (0.2 seconds)
        self.assertGreaterEqual(avg_nonexistent, 0.2)
        self.assertGreaterEqual(avg_active, 0.2)
        self.assertGreaterEqual(avg_inactive, 0.2)

        # Times should be reasonably close to each other
        # We'll allow for some system variation but they should be within 0.15s
        self.assertLess(abs(avg_nonexistent - avg_inactive), 0.15)
        self.assertLess(abs(avg_nonexistent - avg_active), 0.15)
        self.assertLess(abs(avg_inactive - avg_active), 0.15)


class CheckSessionActivationViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.url = reverse("check_session_activation")

    def test_no_pending_activation_returns_false(self):
        """Test that view returns pendingActivation=False when no email in session"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"pendingActivation": False})

    def test_pending_activation_returns_email_and_true(self):
        """Test that view returns pendingActivation=True and email when session has pending activation"""
        # Set up session with pending activation email
        session = self.client.session
        session["pending_activation_email"] = "test_user@example.com"
        session.save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data, {"pendingActivation": True, "email": "test_user@example.com"}
        )

    def test_session_cleared_after_reading(self):
        """Test that pending_activation_email is cleared from session after reading"""
        # Set up session with pending activation email
        session = self.client.session
        session["pending_activation_email"] = "test_user@example.com"
        session.save()

        # First request should return the email
        first_response = self.client.get(self.url)
        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            first_response.data,
            {"pendingActivation": True, "email": "test_user@example.com"},
        )

        # Second request should return pendingActivation=False
        # as the session should be cleared
        second_response = self.client.get(self.url)
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        self.assertEqual(second_response.data, {"pendingActivation": False})

    def test_different_email_values_handled_correctly(self):
        """Test that different email values are handled correctly"""
        test_emails = [
            "user@example.com",
            "user+tag@example.com",
            "user.name@example.co.uk",
            "user-name@sub.domain.com",
        ]

        for email in test_emails:
            # Set up session with pending activation email
            session = self.client.session
            session["pending_activation_email"] = email
            session.save()

            response = self.client.get(self.url)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data, {"pendingActivation": True, "email": email})

            # Verify session is cleared
            second_response = self.client.get(self.url)
            self.assertEqual(second_response.data, {"pendingActivation": False})

    def test_empty_string_email_handled_correctly(self):
        """Test that empty string email is handled correctly"""
        # Set up session with empty string email
        session = self.client.session
        session["pending_activation_email"] = ""
        session.save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"pendingActivation": False})

    def test_none_email_handled_correctly(self):
        """Test that None email is handled correctly"""
        # Set up session with None email
        session = self.client.session
        session["pending_activation_email"] = None
        session.save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"pendingActivation": False})


class ActivationFlowIntegrationTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.check_email_url = reverse("check_email_activation")
        cls.check_session_url = reverse("check_session_activation")

        cls.active_user = UserFactory()
        cls.inactive_user = UserFactory(is_active=False)

    def test_full_activation_flow_inactive_user(self):
        """Test the full flow from CheckEmailActivationView to CheckSessionActivationView for inactive user"""
        with patch("time.sleep"):  # Mock sleep to speed up tests
            # Step 1: Call CheckEmailActivationView with inactive user email
            email_response = self.client.post(
                self.check_email_url, {"email": self.inactive_user.email}, format="json"
            )

            self.assertEqual(email_response.status_code, status.HTTP_200_OK)
            self.assertEqual(
                email_response.data,
                {
                    "status": "success",
                    "message": "If this account exists and is not activated, please check your email for activation instructions.",
                },
            )

            # Step 2: Call CheckSessionActivationView to retrieve the stored email
            session_response = self.client.get(self.check_session_url)

            self.assertEqual(session_response.status_code, status.HTTP_200_OK)
            self.assertEqual(
                session_response.data,
                {"pendingActivation": True, "email": self.inactive_user.email},
            )

            # Step 3: Verify session is cleared after reading
            second_session_response = self.client.get(self.check_session_url)
            self.assertEqual(second_session_response.status_code, status.HTTP_200_OK)
            self.assertEqual(second_session_response.data, {"pendingActivation": False})

    def test_full_activation_flow_active_user(self):
        """Test the full flow from CheckEmailActivationView to CheckSessionActivationView for active user"""
        with patch("time.sleep"):  # Mock sleep to speed up tests
            # Step 1: Call CheckEmailActivationView with active user email
            email_response = self.client.post(
                self.check_email_url, {"email": self.active_user.email}, format="json"
            )

            self.assertEqual(email_response.status_code, status.HTTP_200_OK)
            self.assertEqual(
                email_response.data,
                {
                    "status": "success",
                    "message": "If this account exists and is not activated, please check your email for activation instructions.",
                },
            )

            # Step 2: Call CheckSessionActivationView - should return pendingActivation=False
            # since active users don't get stored in the session
            session_response = self.client.get(self.check_session_url)

            self.assertEqual(session_response.status_code, status.HTTP_200_OK)
            self.assertEqual(session_response.data, {"pendingActivation": False})

    def test_full_activation_flow_nonexistent_user(self):
        """Test the full flow from CheckEmailActivationView to CheckSessionActivationView for nonexistent user"""
        with patch("time.sleep"):  # Mock sleep to speed up tests
            # Step 1: Call CheckEmailActivationView with nonexistent user email
            email_response = self.client.post(
                self.check_email_url,
                {"email": "nonexistent@example.com"},
                format="json",
            )

            self.assertEqual(email_response.status_code, status.HTTP_200_OK)
            self.assertEqual(
                email_response.data,
                {
                    "status": "success",
                    "message": "If this account exists and is not activated, please check your email for activation instructions.",
                },
            )

            # Step 2: Call CheckSessionActivationView - should return pendingActivation=False
            # since nonexistent users don't get stored in the session
            session_response = self.client.get(self.check_session_url)

            self.assertEqual(session_response.status_code, status.HTTP_200_OK)
            self.assertEqual(session_response.data, {"pendingActivation": False})
