from rest_framework import permissions, status
from utils.exceptions import DetailedPermissionDenied


class EditionPermission(permissions.BasePermission):

    def has_permission(self, request, view):

        if not request.user.is_authenticated:
            raise DetailedPermissionDenied(
                detail="Debe estar autenticado para realizar esta acción",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        if view.action in ["list"] and not request.user.is_superuser:

            raise DetailedPermissionDenied(
                detail="Sólo los  superusuarios pueden realizar esta acción",
            )

        return True
