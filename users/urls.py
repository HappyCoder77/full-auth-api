from . import views
from django.urls import path,  include

from rest_framework.routers import DefaultRouter
from .views import DealerStockAPIView, DealerListStockAPIView
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
    path('dealer/stock/total/',
         DealerStockAPIView.as_view(), name='dealer-total-stock'),
    path('dealer/stock/<int:edition_id>/',
         DealerStockAPIView.as_view(), name='dealer-edition-stock'),
    path('dealer/stock/list/',
         DealerListStockAPIView.as_view(), name='dealer-stock-list'),
]
