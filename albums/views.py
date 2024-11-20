
from django.utils import timezone
from rest_framework.exceptions import NotFound
from rest_framework.serializers import ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status, mixins
from editions.models import Edition
from promotions.models import Promotion
from .models import Album
from .permissions import IsAuthenticatedCollector
from .serializers import AlbumSerializer


class UserAlbumListRetrieveView(
        mixins.ListModelMixin,
        mixins.RetrieveModelMixin,
        GenericAPIView):
    """
    Vista de recuperacion de albums.
    GET /api/user-albums/{edition_id}/ => devuelve el álbum perteneciente
    a un colleccionista y edición en curso.
    GET /api/user-albums/ => devuelve una lista de todos
    los álbumes del coleccionista para la promoción en curso.
    Permisos - collector autenticado.
    """
    serializer_class = AlbumSerializer
    permission_classes = [IsAuthenticatedCollector]
    lookup_field = 'edition_id'
    lookup_url_kwarg = lookup_field

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

    def get_queryset(self):
        return Album.objects.filter(collector=self.request.user)

    def get(self, request, *args, **kwargs):
        promotion = self.get_current_promotion()

        if not promotion:
            return Response(
                {'detail': 'No hay ninguna promoción en curso, no es posible la consulta.'},
                status=status.HTTP_200_OK
            )

        edition_id = self.kwargs.get('edition_id')

        if edition_id:
            try:
                edition = Edition.objects.get(pk=edition_id)

            except Edition.DoesNotExist:

                raise NotFound(
                    'No existe ninguna edición con el id suministrado')

            return self.retrieve(request, *args, **kwargs)

        return self.list(request, *args, **kwargs)

    def handle_exception(self, exc):
        return Response(
            {'detail': str(exc)}, status=exc.status_code
        )


class UserAlbumCreateView(mixins.CreateModelMixin, GenericAPIView):
    """
    Vista para la creacion de álbum para edición en curso. 
    Permisos - collector autenticado
    """
    serializer_class = AlbumSerializer
    permission_classes = [IsAuthenticatedCollector]

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

    def post(self, request, *args, **kwargs):
        promotion = self.get_current_promotion()

        if not promotion:
            return Response(
                {'detail': 'No hay ninguna promoción en curso, no es posible esta acción.'},
                status=status.HTTP_200_OK
            )

        edition_id = request.data.get('edition')
        if edition_id:
            try:
                edition = Edition.objects.get(pk=edition_id)
            except Edition.DoesNotExist:
                raise NotFound(
                    'No existe ninguna edición con el id suministrado.'
                )

        return self.create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(collector=self.request.user)

    def handle_exception(self, exc):

        if (isinstance(exc, ValidationError) and
            isinstance(exc.detail, dict) and
                'edition' in exc.detail):
            if 'Este campo es requerido' in str(exc.detail['edition']):
                return Response(
                    {'detail': 'El campo edition es requerido.'},
                    status=exc.status_code
                )

        return Response(
            {'detail': str(exc)}, status=exc.status_code
        )
