from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)

from djoser.social.views import ProviderAuthView
from .models import (RegionalManager, LocalManager,
                     Sponsor, Dealer, BaseProfile)
from .serializers import (RegionalManagerSerializer,
                          LocalManagerSerializer, SponsorSerializer,
                          DealerSerializer, BaseProfileSerializer)
from .permissions import (IsSuperUser, IsRegionalManager,
                          IsLocalManager, IsSponsor, IsCollector)


class CustomProviderAuthView(ProviderAuthView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == 201:
            access_token = request.data.get('access')
            refresh_token = request.data.get('refresh')

            response.set_cookie(
                'access',
                access_token,
                max_age=settings.AUTH_COOKIE_ACCESS_MAX_AGE,
                path=settings.AUTH_COOKIE_PATH,
                secure=settings.AUTH_COOKIE_SECURE,
                httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                samesite=settings.AUTH_COOKIE_SAMESITE
            )

            response.set_cookie(
                'refresh',
                refresh_token,
                max_age=settings.AUTH_COOKIE_ACCESS_MAX_AGE,
                path=settings.AUTH_COOKIE_PATH,
                secure=settings.AUTH_COOKIE_SECURE,
                httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                samesite=settings.AUTH_COOKIE_SAMESITE
            )

        return response


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            access_token = response.data.get('access')
            refresh_token = response.data.get('refresh')

            response.set_cookie(
                'access',
                access_token,
                max_age=settings.AUTH_COOKIE_ACCESS_MAX_AGE,
                path=settings.AUTH_COOKIE_PATH,
                secure=settings.AUTH_COOKIE_SECURE,
                httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                samesite=settings.AUTH_COOKIE_SAMESITE
            )

            response.set_cookie(
                'refresh',
                refresh_token,
                max_age=settings.AUTH_COOKIE_ACCESS_MAX_AGE,
                path=settings.AUTH_COOKIE_PATH,
                secure=settings.AUTH_COOKIE_SECURE,
                httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                samesite=settings.AUTH_COOKIE_SAMESITE
            )

        return response


class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh')

        if refresh_token:
            request.data['refresh'] = refresh_token

        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            access_token = response.data.get('access')

            response.set_cookie(
                'access',
                access_token,
                max_age=settings.AUTH_COOKIE_ACCESS_MAX_AGE,
                path=settings.AUTH_COOKIE_PATH,
                secure=settings.AUTH_COOKIE_SECURE,
                httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                samesite=settings.AUTH_COOKIE_SAMESITE
            )

        return response


class CustomTokenVerifyView(TokenVerifyView):
    def post(self, request, *args, **kwargs):
        access_token = request.COOKIES.get('access')

        if access_token:
            request.data['token'] = access_token

        return super().post(request, *args, **kwargs)


class LogoutView(APIView):
    def post(self, request, *args, **kwargs):
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie('access')
        response.delete_cookie('refresh')

        return response


class RegionalManagerViewSet(viewsets.ModelViewSet):
    """
    Vista para crear RegionalManagers.
    """
    # evitar borrado o actualizacion del registro
    http_method_names = ['get', 'post']
    queryset = RegionalManager.objects.all()
    serializer_class = RegionalManagerSerializer
    permission_classes = [IsSuperUser]

    @action(detail=False, methods=['get'], permission_classes=[IsSuperUser])
    def count(self, request):
        total = self.queryset.count()
        return Response({'total': total})

    def perform_create(self, serializer):
        serializer.save(user=None, created_by=self.request.user)


class LocalManagerViewSet(viewsets.ModelViewSet):
    """
    Vista para crear LocalManagers.
    """
    # evitar borrado o actualizacion del registro
    http_method_names = ['get', 'post']
    queryset = LocalManager.objects.all()
    serializer_class = LocalManagerSerializer
    permission_classes = [IsRegionalManager]

    @action(detail=False, methods=['get'], permission_classes=[IsSuperUser])
    def count(self, request):
        total = self.queryset.count()
        return Response({'total': total})

    @action(detail=False,
            methods=['get'],
            url_path="count-by-creator/(?P<creator_id>\d+)",
            permission_classes=[IsRegionalManager])
    def count_by_creator(self, request, creator_id=None):
        total = self.queryset.filter(created_by_id=creator_id).count()
        return Response({'total': total})

    def perform_create(self, serializer):
        serializer.save(user=None, created_by=self.request.user)


class SponsorViewSet(viewsets.ModelViewSet):
    """
    Vista para crear Sponsors.
    """
    # evitar borrado o actualizacion del registro
    http_method_names = ['get', 'post']
    queryset = Sponsor.objects.all()
    serializer_class = SponsorSerializer
    permission_classes = [IsLocalManager]

    @action(detail=False, methods=['get'], permission_classes=[IsSuperUser])
    def count(self, request):
        total = self.queryset.count()
        return Response({'total': total})

    @action(detail=False,
            methods=['get'],
            url_path="count-by-creator/(?P<creator_id>\d+)",
            permission_classes=[IsLocalManager])
    def count_by_creator(self, request, creator_id=None):
        total = self.queryset.filter(created_by_id=creator_id).count()
        return Response({'total': total})

    def perform_create(self, serializer):
        serializer.save(user=None, created_by=self.request.user)


class DealerViewSet(viewsets.ModelViewSet):
    """
    Vista para crear Dealers.
    """
    # evitar borrado o actualizacion del registro
    http_method_names = ['get', 'post']
    queryset = Dealer.objects.all()
    serializer_class = DealerSerializer
    permission_classes = [IsSponsor]

    @action(detail=False, methods=['get'], permission_classes=[IsSuperUser])
    def count(self, request):
        total = self.queryset.count()
        return Response({'total': total})

    def perform_create(self, serializer):
        serializer.save(user=None, created_by=self.request.user)


class CollectorViewSet(viewsets.ModelViewSet):
    """
    Vista para manejar perfiles de Coleccionistas.
    """
    queryset = BaseProfile.objects.all()
    serializer_class = BaseProfileSerializer
    permission_classes = [IsCollector]

    def get_queryset(self):
        # Filtrar para que un coleccionista solo pueda ver su propio perfil
        return BaseProfile.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        # Verificar si el usuario ya tiene un perfil
        if BaseProfile.objects.filter(user=request.user).exists():
            return Response(
                {"detail": "Ya tienes un perfil creado. Usa el método PUT para actualizarlo."},
                status=status.HTTP_400_BAD_REQUEST
            )
        request.data['email'] = request.user.email
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Asegurarse de que el usuario solo pueda actualizar su propio perfil
        if instance.user != request.user:
            return Response(
                {"detail": "No tienes permiso para editar este perfil."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def me(self, request):
        profile = get_object_or_404(BaseProfile, user=request.user)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

    # Sobrescribir estos métodos para prevenir su uso
    def destroy(self, request, *args, **kwargs):
        return Response(
            {"detail": "No se permite eliminar perfiles de coleccionistas."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def list(self, request, *args, **kwargs):
        return Response(
            {"detail": "No se permite listar todos los perfiles. Usa la acción 'me' para ver tu perfil."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
