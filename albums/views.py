from django.utils import timezone
from django.db import IntegrityError
from rest_framework.exceptions import NotFound
from rest_framework.serializers import ValidationError
from rest_framework.generics import GenericAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, mixins
from editions.models import Edition, Pack, Sticker
from editions.serializers import PackSerializer
from promotions.models import Promotion
from .models import Album, Slot
from .permissions import IsAuthenticatedCollector
from .serializers import AlbumSerializer


class UserAlbumListRetrieveView(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericAPIView
):
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
    lookup_field = "edition_id"
    lookup_url_kwarg = lookup_field

    def get_current_promotion(self):
        now = timezone.now()
        try:
            promotion = Promotion.objects.get(start_date__lte=now, end_date__gte=now)
        except Promotion.DoesNotExist:
            return None

        return promotion

    def get_queryset(self):
        return Album.objects.filter(collector=self.request.user)

    def get(self, request, *args, **kwargs):
        promotion = self.get_current_promotion()

        if not promotion:
            return Response(
                {
                    "detail": "No hay ninguna promoción en curso, no es posible la consulta."
                },
                status=status.HTTP_200_OK,
            )
        # TODO: puede acceder a albumes de ediciones posteriores?
        edition_id = self.kwargs.get("edition_id")

        if edition_id:
            try:
                edition = Edition.objects.get(pk=edition_id)

            except Edition.DoesNotExist:

                raise NotFound("No existe ninguna edición con el id suministrado")

            return self.retrieve(request, *args, **kwargs)

        return self.list(request, *args, **kwargs)

    def handle_exception(self, exc):
        return Response({"detail": str(exc)}, status=exc.status_code)


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
            promotion = Promotion.objects.get(start_date__lte=now, end_date__gte=now)
        except Promotion.DoesNotExist:
            return None

        return promotion

    def post(self, request, *args, **kwargs):
        promotion = self.get_current_promotion()

        if not promotion:
            return Response(
                {
                    "detail": "No hay ninguna promoción en curso, no es posible esta acción."
                },
                status=status.HTTP_200_OK,
            )

        edition_id = request.data.get("edition")
        if edition_id:
            try:
                edition = Edition.objects.get(pk=edition_id)
            except Edition.DoesNotExist:
                raise NotFound("No existe ninguna edición con el id suministrado.")
        try:
            album = Album.objects.get(collector=request.user, edition=edition_id)
            serializer = self.get_serializer(album)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Album.DoesNotExist:
            return self.create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(collector=self.request.user)

    def handle_exception(self, exc):

        if isinstance(exc, IntegrityError):
            return Response(
                {"detail": "El álbum ya existe para esta edición."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            isinstance(exc, ValidationError)
            and isinstance(exc.detail, dict)
            and "edition" in exc.detail
        ):
            if "Este campo es requerido" in str(exc.detail["edition"]):
                return Response(
                    {"detail": "El campo edition es requerido."}, status=exc.status_code
                )

        status_code = getattr(exc, "status_code", status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"detail": str(exc)}, status=status_code)


class AlbumDetailView(RetrieveAPIView):
    serializer_class = AlbumSerializer
    permission_classes = [IsAuthenticatedCollector]

    def get_queryset(self):
        return Album.objects.filter(collector=self.request.user)


class OpenPackView(APIView):
    permission_classes = [IsAuthenticatedCollector]

    def post(self, request, pk):
        try:
            pack = Pack.objects.get(pk=pk, collector=request.user, is_open=False)
        except Pack.DoesNotExist:
            return Response(
                {
                    "detail": "El sobre que se intenta abrir no existe, pertenece a otro coleccionista o ya fué abierto"
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        pack.save()
        pack.open(request.user)

        serializer = PackSerializer(pack)
        return Response(serializer.data)


class PlaceStickerView(APIView):
    permission_classes = [IsAuthenticatedCollector]

    def post(self, request, sticker_id):
        try:
            sticker = Sticker.objects.get(id=sticker_id)
            slot_id = request.data.get("slot_id")
            slot = Slot.objects.get(id=slot_id)

            if sticker.collector != request.user:
                return Response(
                    {"detail": "Solo puedes pegar tus propias barajitas"},
                    status=status.HTTP_403_FORBIDDEN,
                )

            if slot.page.album.collector != request.user:
                return Response(
                    {"detail": "Solo puedes pegar barajitas en tu propio album"},
                    status=status.HTTP_403_FORBIDDEN,
                )

            slot.place_sticker(sticker)

            return Response(
                {
                    "message": "Barajita pegada correctamente",
                    "slot_id": slot.id,
                    "sticker_id": sticker.id,
                },
                status=status.HTTP_200_OK,
            )

        except Sticker.DoesNotExist:
            return Response(
                {"error": "Sticker not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Slot.DoesNotExist:
            return Response(
                {"error": "Slot not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
