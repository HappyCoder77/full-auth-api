from django.http import Http404
from django.utils import timezone
from rest_framework.exceptions import MethodNotAllowed, ValidationError
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework import status
from utils.exceptions import DetailedPermissionDenied
from promotions.models import Promotion
from .permissions import EditionPermission
from .serializers import EditionSerializer
from .models import Edition


class EditionViewSet(ReadOnlyModelViewSet):
    serializer_class = EditionSerializer
    permission_classes = [EditionPermission]
    queryset = Edition.objects.all()

    def get_current_promotion(self):
        now = timezone.now()
        try:
            promotion = Promotion.objects.get(
                start_date__lte=now,
                end_date__gte=now
            )
        except Promotion.DoesNotExist:
            return None

        return promotion

    @action(detail=False, methods=['get'])
    def current_list(self, request):
        promotion = self.get_current_promotion()

        if promotion:
            try:
                editions = Edition.objects.filter(promotion=promotion)
                serializer = self.get_serializer(editions, many=True)

                if not editions.exists():
                    return Response(
                        {'detail': 'No hay ediciones activas para la promoción en curso'},
                        status=status.HTTP_200_OK
                    )

                return Response(serializer.data)
            except Exception as e:
                return Response(
                    {'detail': 'Se produjo un error al obtener las ediciones'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(
            {'detail': 'No hay ninguna promoción en curso'},
            status=status.HTTP_200_OK
        )

    def handle_exception(self, exc):

        if isinstance(exc, DetailedPermissionDenied):
            return Response({'detail': str(exc.detail)}, status=exc.status_code)
        elif isinstance(exc, Http404):
            return Response(
                {'detail': 'No encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )
        elif isinstance(exc, MethodNotAllowed):
            return Response(
                {'detail': 'Método no permitido.'},
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )
        else:
            return Response(
                {
                    'detail': 'Se produjo un error inesperado.',
                    "error": str(exc)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
