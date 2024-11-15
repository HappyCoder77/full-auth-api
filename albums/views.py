from django.shortcuts import get_object_or_404
from django.http import Http404
from rest_framework.exceptions import MethodNotAllowed, ValidationError
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework import status
from .models import Album
from utils.exceptions import DetailedPermissionDenied
from .permissions import AlbumPermission
from .serializers import AlbumSerializer


class AlbumViewSet(ModelViewSet):
    queryset = Album.objects.all()
    serializer_class = AlbumSerializer
    permission_classes = [AlbumPermission]

    def list(self, request, *args, **kwargs):
        """
        Obtiene la lista de todos los álbumes.
        Retorna una colección paginada de álbumes con sus datos básicos.
        Permisos - autenticado y superusuario
        """
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """
        Crea un nuevo álbum.

        Recibe los datos del álbum y retorna el álbum creado.
        Permisos => autenticado y (coleccionista o superusuario)
        """
        return super().create(request, *args, **kwargs)

    def get_object(self):
        collector = self.kwargs.get('pk')
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, collector=collector)
        self.check_object_permissions(self.request, obj)
        return obj

    def retrieve(self, request, *args, **kwargs):
        """
        Obtiene un álbum específico.

        Retorna los detalles completos de un álbum según su ID.
        Permisos => autenticado y (collector.user coincidente con album.collector o superusuario)
        """
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        Actualiza un álbum existente.

        Actualiza todos los campos de un álbum específico.
        Permisos => autenticado y superusuario
        """
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """
        Actualiza parcialmente un álbum.

        Permite actualizar uno o más campos de un álbum específico.
        Permisos => autenticado y (coleccionista o superusuario)
        """
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Elimina un álbum.
        Elimina permanentemente un álbum específico del sistemas.
        Permisos => autenticado y superusuario
        """
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['GET'], url_path='me/list', url_name='me-list')
    def user_albums(self, request):
        """
        Obtiene los álbumes del usuario autenticado.

        Retorna una lista de álbumes pertenecientes al usuario autenticado.
        Permisos => autenticado y (collector o superuser)
        """
        albums = Album.objects.filter(collector=request.user)
        serializer = self.get_serializer(albums, many=True)
        return Response(serializer.data)

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

        elif isinstance(exc, ValidationError):
            if 'non_field_errors' in str(exc).lower():
                message = 'Los campos collector, edition deben formar un conjunto único.'

                if message in exc.detail['non_field_errors']:
                    return Response(
                        {'detail': 'Ya existe un album para este usuario y esta edición'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                return Response(
                    {'detail': 'Se produjo un error de integridad en la base de datos.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {
                    'detail': 'Se produjo un error inesperado.',
                    "error": str(exc)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
