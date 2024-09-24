from . import views
from django.urls import path, re_path, include
from .views import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    CustomTokenVerifyView,
    LogoutView,
    CustomProviderAuthView
)
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'regional-manager-profile', views.RegionalManagerViewSet,
                basename='regional-manager-profile')

urlpatterns = [
    path('register/', include(router.urls)),
    re_path(
        r'^o/(?P<provider>\S+)/$',
        CustomProviderAuthView.as_view(),
        name='provider-auth'
    ),
    path('jwt/create/', CustomTokenObtainPairView.as_view(), name='jwt_create'),
    path('jwt/refresh/', CustomTokenRefreshView.as_view(), name='jwt_refresh'),
    path('jwt/verify/', CustomTokenVerifyView.as_view(), name='jwt_verify'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
