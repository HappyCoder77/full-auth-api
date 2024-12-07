from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.generics import ListCreateAPIView, RetrieveAPIView
from rest_framework.response import Response


from .models import Order
from .permissions import IsAuthenticatedDealer
from .serializers import OrderSerializer


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
