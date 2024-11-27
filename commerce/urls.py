from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import OrderListCreateAPIView, OrderRetrieveAPIView


urlpatterns = [
    path('orders/',
         OrderListCreateAPIView.as_view(), name='order-list-create'),
    path('orders/<int:pk>/',
         OrderRetrieveAPIView.as_view(), name='order-retrieve')
]
