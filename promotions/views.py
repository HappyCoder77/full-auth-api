from .serializers import PromotionSerializer
from rest_framework.response import Response
from django.utils import timezone
from rest_framework import viewsets
from .models import Promotion


class PromotionViewSet(viewsets.ModelViewSet):
    """
    Vista para visualizar promocion activa
    """
    # evitar borrado o actualizacion del registro
    serializer_class = PromotionSerializer

    def get_queryset(self):
        now = timezone.now()
        return Promotion.objects.filter(
            start_date__lte=now,
            end_date__gte=now
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if queryset.exists():
            serializer = self.get_serializer(queryset.first())
            return Response([serializer.data])
        return Response([])
