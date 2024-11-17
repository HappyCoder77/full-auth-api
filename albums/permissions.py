from rest_framework import permissions, status
from utils.exceptions import DetailedPermissionDenied


class AlbumPermission(permissions.BasePermission):

    def has_permission(self, request, view):

        if not request.user.is_authenticated:
            raise DetailedPermissionDenied(
                detail="Debe estar autenticado para realizar esta acción",
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        if view.action in ['create', 'retrieve', 'partial_update', 'me-albums', 'get_or_create']:

            if not request.user.is_collector and not request.user.is_superuser:
                raise DetailedPermissionDenied(
                    detail="Solo los coleccionistas o superusuarios pueden realizar esta acción"
                )

            return True

        if view.action in ['list', 'update', 'destroy']:
            if not request.user.is_superuser:
                raise DetailedPermissionDenied(
                    "Sólo los  superusuarios pueden realizar esta acción")

            return True

        return True

    def has_object_permission(self, request, view, obj):

        if obj.collector != request.user and not request.user.is_superuser:
            raise DetailedPermissionDenied(
                detail="Solo puedes ver tu propio álbum"
            )

        return True
