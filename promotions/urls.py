from . import views
from django.urls import path, include
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register(r'promotion', views.PromotionViewSet,
                basename='promotion')


urlpatterns = [
    path('', include(router.urls)),
]
