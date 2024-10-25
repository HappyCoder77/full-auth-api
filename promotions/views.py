from .serializers import PromotionSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from rest_framework import viewsets
from .models import Promotion


class PromotionViewSet(viewsets.ModelViewSet):
    """
    Vista para visualizar promocion activa
    """
    # evitar borrado o actualizacion del registro
    queryset = Promotion.objects.all()
    serializer_class = PromotionSerializer

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

    @action(detail=True, methods=['get'])
    def current(self, request):
        promotion = self.get_current_promotion()

        if promotion:
            serializer = self.get_serializer(promotion)
            return Response(serializer.data)

        return Response(None)
