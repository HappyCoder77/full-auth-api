from django.conf import settings
from rest_framework.views import APIView
from rest_framework.exceptions import MethodNotAllowed
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
                     Sponsor, Dealer, Collector)

from .serializers import (RegionalManagerSerializer,
                          LocalManagerSerializer, SponsorSerializer,
                          DealerSerializer, CollectorSerializer)

from .permissions import (IsSuperUser, IsRegionalManagerOrSuperUser,
                          IsLocalManagerOrSuperUser, IsSponsorOrSuperUser, CollectorPermission, DetailedPermissionDenied)

# TODO: agregar docstrings a las actions para mejorar la documentacion


class CustomProviderAuthView(ProviderAuthView):
    # TODO: considera eliminar esto ya que no se esta usando
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

    @action(detail=False, methods=['get'])
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
    serializer_class = LocalManagerSerializer
    permission_classes = [IsRegionalManagerOrSuperUser]

    def get_queryset(self):

        if self.request.user.is_regionalmanager:
            return LocalManager.objects.filter(created_by=self.request.user)

        return LocalManager.objects.all()

    @action(detail=False, methods=['get'])
    def count(self, request):
        total = self.get_queryset().count()
        return Response({'total': total})

    def perform_create(self, serializer):
        serializer.save(user=None, created_by=self.request.user)


class SponsorViewSet(viewsets.ModelViewSet):
    """
    Vista para crear Sponsors.
    """
    # evitar borrado o actualizacion del registro
    http_method_names = ['get', 'post']
    serializer_class = SponsorSerializer
    permission_classes = [IsLocalManagerOrSuperUser]

    def get_queryset(self):

        if self.request.user.is_localmanager:
            return Sponsor.objects.filter(created_by=self.request.user)

        return Sponsor.objects.all()

    @action(detail=False, methods=['get'])
    def count(self, request):
        total = self.get_queryset().count()
        return Response({'total': total})

    def perform_create(self, serializer):
        serializer.save(user=None, created_by=self.request.user)


class DealerViewSet(viewsets.ModelViewSet):
    """
    Vista para crear Dealers.
    """
    # evitar borrado o actualizacion del registro
    http_method_names = ['get', 'post']
    serializer_class = DealerSerializer
    permission_classes = [IsSponsorOrSuperUser]

    def get_queryset(self):

        if self.request.user.is_sponsor:
            return Dealer.objects.filter(created_by=self.request.user)

        return Dealer.objects.all()

    @action(detail=False, methods=['get'])
    def count(self, request):
        total = self.get_queryset().count()
        return Response({'total': total})

    def perform_create(self, serializer):
        serializer.save(user=None, created_by=self.request.user)


class CollectorViewSet(viewsets.ModelViewSet):
    """
    Vista para manejar perfiles de Coleccionistas.
    """
    http_method_names = ['get', 'post', 'put', 'patch']
    serializer_class = CollectorSerializer
    permission_classes = [CollectorPermission]
    queryset = Collector.objects.all()

    @ action(detail=False, methods=['get'])
    def count(self, request):
        """Devuelve el total de collectors existentes"""
        total = self.queryset.count()
        return Response({'total': total})

    def create(self, request, *args, **kwargs):
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
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)

    @ action(detail=False, methods=['get'])
    def me(self, request):
        profile = get_object_or_404(Collector, user=request.user)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

    def handle_exception(self, exc):
        if isinstance(exc, DetailedPermissionDenied):
            return Response({'detail': str(exc.detail)}, status=exc.status_code)

        return super().handle_exception(exc)
