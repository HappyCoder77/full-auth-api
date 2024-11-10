from django.shortcuts import get_object_or_404
from django.http import Http404
from rest_framework.exceptions import MethodNotAllowed
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

    def handle_exception(self, exc):
        if isinstance(exc, DetailedPermissionDenied):
            return Response({'detail': str(exc.detail)}, status=exc.status_code)

        elif isinstance(exc, Http404):
            return Response({'detail': 'No encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        elif isinstance(exc, MethodNotAllowed):
            return Response({'detail': 'Método no permitido.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        else:
            return Response(
                {
                    'detail': 'Se produjo un error inesperado.',
                    "error": str(exc)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
