from rest_framework.routers import DefaultRouter
from djoser import views
from django.urls import path, include
from .views import (CustomTokenObtainPairView,
                    CustomTokenRefreshView, CustomTokenVerifyView, LogoutView)

router = DefaultRouter()
router.register('useraccount', views.UserViewSet, basename='useraccount')
urlpatterns = [
    path('', include(router.urls)),
    path('jwt/create/', CustomTokenObtainPairView.as_view(), name='jwt_create'),
    path('jwt/refresh/', CustomTokenRefreshView.as_view(), name='jwt_refresh'),
    path('jwt/verify/', CustomTokenVerifyView.as_view(), name='jwt_verify'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
