from django.http import Http404
from .serializers import PromotionSerializer
from rest_framework.exceptions import MethodNotAllowed, APIException
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from rest_framework import viewsets, status
from .models import Promotion
from utils.exceptions import DetailedPermissionDenied
from .permissions import PromotionPermission


class PromotionViewSet(viewsets.ModelViewSet):
    """
    Vista para manejar las promociones
    """

    # evitar borrado o actualizacion del registro
    queryset = Promotion.objects.all()
    serializer_class = PromotionSerializer
    permission_classes = [PromotionPermission]

    def get_current_promotion(self):
        now = timezone.now().date()

        try:
            promotion = Promotion.objects.get(start_date__lte=now, end_date__gte=now)
        except Promotion.DoesNotExist:
            return None

        return promotion

    @action(detail=False, methods=["get"])
    def current(self, request):
        promotion = self.get_current_promotion()

        if promotion:
            serializer = self.get_serializer(promotion)
            return Response(serializer.data)

        return Response(None, status=status.HTTP_200_OK)

    def handle_exception(self, exc):

        if isinstance(exc, DetailedPermissionDenied):
            return Response({"detail": str(exc.detail)}, status=exc.status_code)

        elif isinstance(exc, Http404):
            return Response(
                {"detail": "No encontrado."}, status=status.HTTP_404_NOT_FOUND
            )

        elif isinstance(exc, MethodNotAllowed):
            return Response(
                {"detail": "Método no permitido."},
                status=status.HTTP_405_METHOD_NOT_ALLOWED,
            )

        return Response(
            {"detail": "Se produjo un error inesperado."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    @action(detail=False, methods=["get"])
    def force_error(self, request):
        raise APIException("Error forzado para prueba.")
