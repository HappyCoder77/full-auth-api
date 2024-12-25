from django.urls import path
from .views import (
    OrderListCreateAPIView,
    OrderRetrieveAPIView,
    PaymentListAPIView,
    PaymentCreateView,
    MobilePaymentCreateView,
    PaymentOptionsView,
    MobilePaymentOptionsView,
    LastDealerBalanceView,
)


urlpatterns = [
    path("orders/", OrderListCreateAPIView.as_view(), name="order-list-create"),
    path("orders/<int:pk>/", OrderRetrieveAPIView.as_view(), name="order-retrieve"),
    path("payments/", PaymentListAPIView.as_view(), name="payment-list"),
    path("payments/create/", PaymentCreateView.as_view(), name="payment-create"),
    path(
        "payments/mobile/create/",
        MobilePaymentCreateView.as_view(),
        name="mobile-payment-create",
    ),
    path("payments/options/", PaymentOptionsView.as_view(), name="payment-options"),
    path(
        "payments/mobile/options/",
        MobilePaymentOptionsView.as_view(),
        name="mobile-payment-options",
    ),
    path("last-balance/", LastDealerBalanceView.as_view(), name="last-dealer-balance"),
]
