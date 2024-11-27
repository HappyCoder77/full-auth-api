from rest_framework import permissions, status
from utils.exceptions import DetailedPermissionDenied


class IsAuthenticatedDealer(permissions.BasePermission):

    def has_permission(self, request, view):

        if not request.user.is_authenticated:
            raise DetailedPermissionDenied(
                detail="Debe iniciar sesión para realizar esta acción",
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        if not request.user.is_dealer:
            raise DetailedPermissionDenied(
                detail="Solo los detallistas pueden realizar esta acción"
            )

        return True
