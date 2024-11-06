from rest_framework import permissions, status

from users.permissions import DetailedPermissionDenied


class PromotionPermission(permissions.BasePermission):
    def has_permission(self, request, view):

        if not request.user.is_authenticated:
            raise DetailedPermissionDenied(
                detail="Debe estar autenticado para realizar esta acción.",
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        if view.action in ['list', 'retrieve', 'create', 'update', 'patch', 'destroy']:
            if not request.user.is_superuser:
                raise DetailedPermissionDenied(
                    detail="Sólo un superusuario puede realizar esta acción."
                )

        return True

    def has_object_permission(self, request, view, obj):

        if not request.user.is_superuser:

            if request.method not in permissions.SAFE_METHODS:
                raise DetailedPermissionDenied(
                    detail="Esta acción esta reservada a los supersuarios"
                )

        return True
