from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.mixins import ListModelMixin
from rest_framework.views import APIView
from rest_framework.generics import (
    GenericAPIView,
    ListCreateAPIView,
    RetrieveAPIView,
    CreateAPIView,
)
from rest_framework.response import Response
from promotions.utils import (
    promotion_is_running,
    get_current_promotion,
    get_last_promotion,
)
from .models import Order, Payment, MobilePayment, DealerBalance
from .permissions import IsAuthenticatedDealer
from .serializers import (
    OrderSerializer,
    PaymentSerializer,
    MobilePaymentSerializer,
    DealerBalanceSerializer,
    SaleSerializer,
)


class OrderListCreateAPIView(ListCreateAPIView):
    permission_classes = [IsAuthenticatedDealer]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(dealer=self.request.user)

    def perform_create(self, serializer):
        serializer.save(dealer=self.request.user)

    def handle_exception(self, exc):

        if isinstance(exc, DjangoValidationError):

            if isinstance(exc.message_dict, dict) and "edition" in exc.message_dict:
                if "Este campo no puede estar vacío." in str(exc.message_dict):
                    return Response(
                        {"detail": "El campo edition no puede estar vacío"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            return Response(
                {"detail": exc.messages[0] if hasattr(exc, "messages") else str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if isinstance(exc, DRFValidationError):

            if "edition" in exc.detail:
                return Response(
                    {"detail": "No existe ninguna edición con el id suministrado"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        status_code = getattr(exc, "status_code", status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"detail": str(exc)}, status=status_code)


class OrderRetrieveAPIView(RetrieveAPIView):
    permission_classes = [IsAuthenticatedDealer]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(dealer=self.request.user)


class PaymentListAPIView(ListModelMixin, GenericAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticatedDealer]

    def get_queryset(self):
        user = self.request.user
        last_promotion = get_last_promotion()

        if last_promotion:
            return Payment.objects.filter(
                dealer=user, payment_date__gte=last_promotion.end_date, status="pending"
            )

        return Payment.objects.filter(dealer=user, status="pending")

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        if not queryset.exists():
            return Response(
                {"detail": "No hay pagos registrados."},
                status=status.HTTP_204_NO_CONTENT,
            )

        return self.list(request, *args, **kwargs)


class PaymentCreateView(CreateAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticatedDealer]

    def perform_create(self, serializer):
        serializer.save(dealer=self.request.user, payment_type="bank")


class MobilePaymentCreateView(CreateAPIView):
    serializer_class = MobilePaymentSerializer
    permission_classes = [IsAuthenticatedDealer]

    def perform_create(self, serializer):
        serializer.save(dealer=self.request.user, payment_type="mobile")

    def handle_exception(self, exc):
        if isinstance(exc, DRFValidationError):
            if hasattr(exc.detail, "get") and exc.detail.get("reference"):
                return Response(
                    {"detail": "Esta referencia ya existe."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return super().handle_exception(exc)


class PaymentOptionsView(APIView):
    http_method_names = ["get"]
    permission_classes = [IsAuthenticatedDealer]

    def get(self, request, format=None):
        options = {
            "banks": dict(Payment.BANKS),
            "payment_status": dict(Payment.PAYMENT_STATUS),
        }
        return Response(options, status=status.HTTP_200_OK)


class MobilePaymentOptionsView(PaymentOptionsView):

    def get(self, request, format=None):
        options = {
            "phone_codes": dict(MobilePayment.PHONE_CODES),
        }
        return Response(options, status=status.HTTP_200_OK)


class DealerBalanceView(APIView):
    permission_classes = [IsAuthenticatedDealer]

    def get(self, request):
        """
        Retrieve the last balance for the current dealer.

        This method fetches the most recent balance entry for the dealer
        associated with the current request user. If a balance entry is found,
        it is serialized and returned in the response. If no balance entry is
        found, a 404 Not Found response is returned with an appropriate message.

        Args:
            request (Request): The HTTP request object.

        Returns:
            Response: A Response object containing the serialized balance data
            or an error message.
        """
        user = request.user
        balance = (
            DealerBalance.objects.filter(dealer=user).order_by("-start_date").first()
        )

        if balance:
            serializer = DealerBalanceSerializer(balance)
            return Response(serializer.data)

        return Response(
            {"detail": "No se encontró ningún balance para el usuario actual."},
            status=status.HTTP_404_NOT_FOUND,
        )


class SaleCreateView(CreateAPIView):
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticatedDealer]

    def perform_create(self, serializer):
        serializer.save(dealer=self.request.user)


class RequestSurprisePrize(APIView):
    pass
