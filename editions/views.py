from django.http import Http404
from django.utils import timezone
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.views import APIView
from rest_framework import status
from utils.exceptions import DetailedPermissionDenied
from albums.permissions import IsAuthenticatedCollector
from promotions.models import Promotion
from .permissions import EditionPermission
from .serializers import EditionSerializer
from .models import Edition, Sticker
from django.core.exceptions import ValidationError as DjangoValidationError


class EditionViewSet(ReadOnlyModelViewSet):
    serializer_class = EditionSerializer
    permission_classes = [EditionPermission]
    queryset = Edition.objects.all()

    def get_current_promotion(self):
        now = timezone.now()
        try:
            promotion = Promotion.objects.get(start_date__lte=now, end_date__gte=now)
        except Promotion.DoesNotExist:
            return None

        return promotion

    @action(detail=False, methods=["get"])
    def current_list(self, request):
        promotion = self.get_current_promotion()

        if not promotion:
            return Response(
                {"detail": "No hay ninguna promoción en curso"},
                status=status.HTTP_404_NOT_FOUND,
            )

        editions = Edition.objects.filter(promotion=promotion)

        if not editions.exists():
            return Response(
                {"detail": "No hay ediciones activas para la promoción en curso"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            serializer = self.get_serializer(editions, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"detail": "Se produjo un error al obtener las ediciones"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

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
        else:
            return Response(
                {"detail": "Se produjo un error inesperado.", "error": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class RescueStickerView(APIView):
    permission_classes = [IsAuthenticatedCollector]

    def post(self, request, sticker_id):
        try:
            sticker = Sticker.objects.get(id=sticker_id)
            sticker.rescue(request.user)
            return Response(status=status.HTTP_200_OK)
        except DjangoValidationError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)
        except Sticker.DoesNotExist:
            return Response(
                {"detail": "Sticker not found"}, status=status.HTTP_404_NOT_FOUND
            )
