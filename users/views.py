from django.http import Http404
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, viewsets
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404

from collection_manager.models import Collection
from promotions.models import Promotion

from .models import RegionalManager, LocalManager, Sponsor, Dealer, Collector

from .serializers import (
    RegionalManagerSerializer,
    LocalManagerSerializer,
    SponsorSerializer,
    DealerSerializer,
    CollectorSerializer,
)

from .permissions import (
    IsSuperUser,
    IsRegionalManagerOrSuperUser,
    IsLocalManagerOrSuperUser,
    IsSponsorOrSuperUser,
    CollectorPermission,
    DetailedPermissionDenied,
    IsAuthenticatedDealer,
)

# TODO: agregar docstrings a las actions para mejorar la documentacion


class RegionalManagerViewSet(viewsets.ModelViewSet):
    """
    Vista para crear RegionalManagers.
    """

    # evitar borrado o actualizacion del registro
    http_method_names = ["get", "post"]
    queryset = RegionalManager.objects.all()
    serializer_class = RegionalManagerSerializer
    permission_classes = [IsSuperUser]

    @action(detail=False, methods=["get"])
    def count(self, request):
        total = self.queryset.count()
        return Response({"total": total})

    def perform_create(self, serializer):
        serializer.save(user=None, created_by=self.request.user)


class LocalManagerViewSet(viewsets.ModelViewSet):
    """
    Vista para crear LocalManagers.
    """

    # evitar borrado o actualizacion del registro
    http_method_names = ["get", "post"]
    serializer_class = LocalManagerSerializer
    permission_classes = [IsRegionalManagerOrSuperUser]

    def get_queryset(self):

        if self.request.user.is_regionalmanager:
            return LocalManager.objects.filter(created_by=self.request.user)

        return LocalManager.objects.all()

    @action(detail=False, methods=["get"])
    def count(self, request):
        total = self.get_queryset().count()
        return Response({"total": total})

    def perform_create(self, serializer):
        serializer.save(user=None, created_by=self.request.user)


class SponsorViewSet(viewsets.ModelViewSet):
    """
    Vista para crear Sponsors.
    """

    # evitar borrado o actualizacion del registro
    http_method_names = ["get", "post"]
    serializer_class = SponsorSerializer
    permission_classes = [IsLocalManagerOrSuperUser]

    def get_queryset(self):

        if self.request.user.is_localmanager:
            return Sponsor.objects.filter(created_by=self.request.user)

        return Sponsor.objects.all()

    @action(detail=False, methods=["get"])
    def count(self, request):
        total = self.get_queryset().count()
        return Response({"total": total})

    def perform_create(self, serializer):
        serializer.save(user=None, created_by=self.request.user)


class DealerViewSet(viewsets.ModelViewSet):
    """
    Vista para crear Dealers.
    """

    # evitar borrado o actualizacion del registro
    http_method_names = ["get", "post"]
    serializer_class = DealerSerializer
    permission_classes = [IsSponsorOrSuperUser]

    def get_queryset(self):

        if self.request.user.is_sponsor:
            return Dealer.objects.filter(created_by=self.request.user)

        return Dealer.objects.all()

    @action(detail=False, methods=["get"])
    def count(self, request):
        total = self.get_queryset().count()
        return Response({"total": total})

    def perform_create(self, serializer):
        serializer.save(user=None, created_by=self.request.user)


class DealerStockAPIView(APIView):
    permission_classes = [IsAuthenticatedDealer]

    def get(self, request, collection_id):

        if not Promotion.objects.is_running():
            return Response(
                {"detail": "No hay ninguna promoción en curso."},
                status=status.HTTP_404_NOT_FOUND,
            )

        collections = Collection.objects.get_current_list()

        if not collections:
            return Response(
                {"detail": "No se han creado colecciones para la promoción en curso."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not collections.filter(id=collection_id).exists():
            return Response(
                {"detail": "No hay ninguna colección activa con el id suministrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        dealer = Dealer.objects.get(user=request.user)
        stock = dealer.get_pack_stock(collection_id)
        return Response({"stock": stock})

    def handle_exception(self, exc):
        status_code = getattr(exc, "status_code", status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"detail": str(exc)}, status=status_code)


class DealerListStockAPIView(APIView):
    permission_classes = [IsAuthenticatedDealer]

    def get(self, request):

        if not Promotion.objects.is_running():
            return Response(
                {"detail": "No hay ninguna promoción en curso."},
                status=status.HTTP_404_NOT_FOUND,
            )

        dealer = Dealer.objects.get(user=request.user)
        collectionStockList = []
        collections = Collection.objects.get_current_list()

        if not collections:
            return Response(
                {"detail": "No se han creado colecciones para la promoción en curso."},
                status=status.HTTP_404_NOT_FOUND,
            )
        for collection in collections:
            collectionStockList.append(
                {
                    "id": collection.id,
                    "name": collection.theme.name,
                    "stock": dealer.get_pack_stock(collection.id),
                }
            )

        return Response(collectionStockList)

    def handle_exception(self, exc):
        status_code = getattr(exc, "status_code", status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"detail": str(exc)}, status=status_code)


class CollectorViewSet(viewsets.ModelViewSet):
    """
    Vista para manejar perfiles de Coleccionistas.
    """

    http_method_names = ["get", "post", "put", "patch"]
    serializer_class = CollectorSerializer
    permission_classes = [CollectorPermission]
    queryset = Collector.objects.all()

    @action(detail=False, methods=["get"])
    def count(self, request):
        """Devuelve el total de collectors existentes"""
        total = self.queryset.count()
        return Response({"total": total})

    def create(self, request, *args, **kwargs):
        request.data["email"] = request.user.email
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def me(self, request):
        """
        Acción que permite ver el perfil de coleccionista del usuario actual si lo tuviese.
        difiere del endpoint detail en que el argumento esta implícito y no necesita ser
        enviado en la url y que sólo el propietario del perfil puede realizar la acción.
        """
        profile = get_object_or_404(Collector, user=request.user)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

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


class CollectorLookupView(APIView):

    def get(self, request):
        email = request.query_params.get("email")

        try:
            collector = Collector.objects.get(email=email)
            return Response(
                CollectorSerializer(collector).data, status=status.HTTP_200_OK
            )

        except Collector.DoesNotExist:
            return Response(
                {"detail": "No existe un coleccionista con el correo ingresado"},
                status=status.HTTP_404_NOT_FOUND,
            )
