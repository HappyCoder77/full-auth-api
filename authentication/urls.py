from django.urls import path, include
from .views import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    CustomTokenVerifyView,
    LogoutView,
    password_help,
)

urlpatterns = [
    path("", include("djoser.urls")),
    path("password-help/", password_help, name="password-help"),
    path("jwt/create/", CustomTokenObtainPairView.as_view(), name="jwt_create"),
    path("jwt/refresh/", CustomTokenRefreshView.as_view(), name="jwt_refresh"),
    path("jwt/verify/", CustomTokenVerifyView.as_view(), name="jwt_verify"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
