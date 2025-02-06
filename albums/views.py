from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.db.models import Min
from rest_framework.exceptions import NotFound, ValidationError
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.generics import GenericAPIView, RetrieveAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, mixins
from editions.models import Edition, Pack, Sticker
from editions.utils import get_current_promotion, get_current_editions
from editions.serializers import (
    PackSerializer,
    StickerPrizeSerializer,
    StickerSerializer,
)


from promotions.models import Promotion
from .models import Album, Slot, Page, PagePrize
from users.models import Collector
from .permissions import IsAuthenticatedCollector, HasEnoughTickets
from .serializers import AlbumSerializer, PagePrizeSerializer


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


class DiscoverStickerPrizeView(APIView):
    permission_classes = [IsAuthenticatedCollector]

    def post(self, request, sticker_id):
        try:
            sticker = Sticker.objects.get(id=sticker_id)

            if sticker.collector != request.user:
                return Response(
                    {
                        "detail": "Solo puedes descubrir premios de tus propias barajitas"
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            try:
                prize = sticker.discover_prize()
                return Response(
                    StickerPrizeSerializer(prize).data, status=status.HTTP_201_CREATED
                )
            except DjangoValidationError as e:
                return Response(
                    {"detail": e.message}, status=status.HTTP_400_BAD_REQUEST
                )

        except Sticker.DoesNotExist:
            return Response(
                {"error": "Sticker not found"}, status=status.HTTP_404_NOT_FOUND
            )


class CreatePagePrizeView(APIView):
    permission_classes = [IsAuthenticatedCollector]

    def post(self, request, page_id):
        try:
            page = Page.objects.get(id=page_id)

            if page.album.collector != request.user:
                return Response(
                    {"detail": "Solo puedes crear premios de tus propias colecciones"},
                    status=status.HTTP_403_FORBIDDEN,
                )

            try:
                prize = page.create_prize()
                return Response(
                    PagePrizeSerializer(prize).data, status=status.HTTP_201_CREATED
                )

            except DjangoValidationError as e:
                if hasattr(e, "message_dict"):
                    error_message = e.message_dict
                else:
                    error_message = {"detail": e.message}
                return Response(error_message, status=status.HTTP_400_BAD_REQUEST)

        except Page.DoesNotExist:
            return Response(
                {"detail": "Page not found"}, status=status.HTTP_404_NOT_FOUND
            )


class PagePrizeListAPIView(ListAPIView):
    serializer_class = PagePrizeSerializer
    permission_classes = [IsAuthenticatedCollector]
    http_method_names = ["get"]

    def get_queryset(self):
        query = PagePrize.objects.filter(
            page__album__collector=self.request.user
        ).order_by("-id")
        return query if query.exists() else PagePrize.objects.none()


class RescuePoolView(ListAPIView):
    serializer_class = StickerSerializer
    permission_classes = [IsAuthenticatedCollector, HasEnoughTickets]
    http_method_names = ["get"]

    def get_queryset(self):
        with transaction.atomic():
            current_promotion = get_current_promotion()

            if not current_promotion:
                raise NotFound(
                    "No hay ninguna promoción en curso, no es posible la consulta."
                )

            current_editions = get_current_editions()

            if not current_editions:
                raise NotFound("No se han creado ediciones para la promoción en curso.")

            user = self.request.user
            collector_profile = Collector.objects.select_for_update().get(user=user)
            collector_profile.rescue_tickets -= 3
            collector_profile.save()

        base_queryset = (
            Sticker.objects.select_for_update()
            .filter(is_repeated=True, pack__box__edition__in=current_editions)
            .exclude(collector=user)
            .exclude(
                coordinate__in=user.stickers.filter(
                    pack__box__edition__in=current_editions
                ).values("coordinate")
            )
        )

        ids_queryset = (
            base_queryset.values("coordinate")
            .annotate(min_id=Min("id"))
            .values("min_id")
        )
        queryset = Sticker.objects.filter(id__in=ids_queryset)

        return queryset if queryset.exists() else Sticker.objects.none()
