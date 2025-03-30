import time
import random
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import (
    UserAttributeSimilarityValidator,
    MinimumLengthValidator,
    CommonPasswordValidator,
    NumericPasswordValidator,
)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            access_token = response.data.get("access")
            refresh_token = response.data.get("refresh")

            response.set_cookie(
                "access",
                access_token,
                max_age=settings.AUTH_COOKIE_ACCESS_MAX_AGE,
                path=settings.AUTH_COOKIE_PATH,
                secure=settings.AUTH_COOKIE_SECURE,
                httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                samesite=settings.AUTH_COOKIE_SAMESITE,
            )

            response.set_cookie(
                "refresh",
                refresh_token,
                max_age=settings.AUTH_COOKIE_ACCESS_MAX_AGE,
                path=settings.AUTH_COOKIE_PATH,
                secure=settings.AUTH_COOKIE_SECURE,
                httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                samesite=settings.AUTH_COOKIE_SAMESITE,
            )

        return response


class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh")

        if refresh_token:
            request.data["refresh"] = refresh_token

        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            access_token = response.data.get("access")

            response.set_cookie(
                "access",
                access_token,
                max_age=settings.AUTH_COOKIE_ACCESS_MAX_AGE,
                path=settings.AUTH_COOKIE_PATH,
                secure=settings.AUTH_COOKIE_SECURE,
                httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                samesite=settings.AUTH_COOKIE_SAMESITE,
            )

        return response


class CustomTokenVerifyView(TokenVerifyView):
    def post(self, request, *args, **kwargs):
        access_token = request.COOKIES.get("access")

        if access_token:
            request.data["token"] = access_token

        return super().post(request, *args, **kwargs)


class LogoutView(APIView):
    def post(self, request, *args, **kwargs):
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie("access")
        response.delete_cookie("refresh")

        return response


@api_view(["GET"])
@permission_classes([AllowAny])
def password_help(request):
    validators = [
        UserAttributeSimilarityValidator(),
        MinimumLengthValidator(),
        CommonPasswordValidator(),
        NumericPasswordValidator(),
    ]

    help_texts = [validator.get_help_text() for validator in validators]
    return Response(help_texts)


class CheckEmailActivationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        start_time = time.time()
        email = request.data.get("email")

        if not email:
            # Add a small random delay for consistency
            time.sleep(random.uniform(0.1, 0.3))
            return Response({"error": "Email is required"}, status=400)

        # For security, ALWAYS return the same structure
        # regardless of whether the email exists or not
        response_data = {
            "status": "success",
            "message": "If this account exists and is not activated, please check your email for activation instructions.",
        }

        # Internally, we'll check if the user exists and is not active
        # but we won't reveal this information directly in the response
        try:
            user = User.objects.get(email=email)
            # Store this information in the session instead of returning it
            # This way the frontend can use it without exposing it in the API
            if not user.is_active:
                request.session["pending_activation_email"] = email
                request.session.save()
        except User.DoesNotExist:
            # Do nothing special, return the same generic response
            pass

        # Ensure consistent response time to prevent timing attacks
        elapsed = time.time() - start_time
        if elapsed < 0.2:  # Ensure minimum response time of 200ms
            time.sleep(0.2 - elapsed + random.uniform(0, 0.1))

        return Response(response_data)


# Add this additional endpoint to check the session
class CheckSessionActivationView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        pending_activation_email = request.session.get("pending_activation_email")

        # Clear the session after reading it (one-time use)
        if pending_activation_email:
            del request.session["pending_activation_email"]
            request.session.save()

            return Response(
                {"pendingActivation": True, "email": pending_activation_email}
            )

        return Response({"pendingActivation": False})
