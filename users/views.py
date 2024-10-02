from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)

from djoser.social.views import ProviderAuthView
from .models import RegionalManager, LocalManager, Sponsor, Dealer
from .serializers import (RegionalManagerSerializer,
                          LocalManagerSerializer, SponsorSerializer, DealerSerializer)
from .permissions import IsSuperUser, IsRegionalManager, IsLocalManager, IsSponsor


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

    def perform_create(self, serializer):
        serializer.save(user=None, created_by=self.request.user)
