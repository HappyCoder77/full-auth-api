from django.urls import path
from .views import (
    OrderListCreateAPIView,
    OrderRetrieveAPIView,
    PaymentListAPIView,
    PaymentCreateView,
    MobilePaymentCreateView,
    PaymentOptionsView,
    MobilePaymentOptionsView,
    DealerBalanceView,
    SaleCreateView,
    RequestSurprisePrizeView,
    SurprizePriseListApiView,
    ClaimPagePrizeView,
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
    path("dealer-balance/", DealerBalanceView.as_view(), name="dealer-balance"),
    path("sales/create/", SaleCreateView.as_view(), name="sale-create"),
    path(
        "prizes/surprise/request/<int:stickerprize_id>",
        RequestSurprisePrizeView.as_view(),
        name="request-surprise-prize",
    ),
    path(
        "prizes/surprise/list",
        SurprizePriseListApiView.as_view(),
        name="surprise-prize-list",
    ),
    path(
        "prizes/page/<int:page_prize_id>/claim/",
        ClaimPagePrizeView.as_view(),
        name="claim-page-prize",
    ),
]
