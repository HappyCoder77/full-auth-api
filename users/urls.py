from . import views
from django.urls import path,  include

from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r'regional-manager', views.RegionalManagerViewSet,
                basename='regional-manager')
router.register(r'local-manager', views.LocalManagerViewSet,
                basename='local-manager')
router.register(r'sponsor', views.SponsorViewSet,
                basename='sponsor')
router.register(r'dealer', views.DealerViewSet,
                basename='dealer')
router.register(r'collector', views.CollectorViewSet,
                basename='collector')

urlpatterns = [
    path('', include(router.urls)),

]
