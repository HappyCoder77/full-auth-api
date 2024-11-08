from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import AlbumViewSet

router = DefaultRouter()
router.register(r'album', AlbumViewSet, basename='album')

urlpatterns = [
    path('', include(router.urls)),
]
