from rest_framework import permissions, status
from rest_framework.exceptions import APIException


class DetailedPermissionDenied(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "No tienes permiso para ejecutar esta acción"
    default_code = "permission denied"

    def __init__(self, detail=None, code=None, status_code=None):
        super().__init__(detail, code)

        if status_code is not None:
            self.status_code = status_code


class IsSuperUser(permissions.BasePermission):
    """
    Permite el acceso solo a los superusuarios.
    """

    def has_permission(self, request, view):
        return request.user.is_superuser


class IsRegionalManagerOrSuperUser(permissions.BasePermission):
    """
    Permite el acceso solo a los gerentes regionales.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.is_regionalmanager or request.user.is_superuser)


class IsLocalManagerOrSuperUser(permissions.BasePermission):
    """
    Permite el acceso solo a los gerentes regionales.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.is_localmanager or request.user.is_superuser)


class IsSponsorOrSuperUser(permissions.BasePermission):
    """
    Permite el acceso solo a los gerentes regionales.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.is_sponsor or request.user.is_superuser)


class CollectorPermission(permissions.BasePermission):
    def has_permission(self, request, view):

        if not request.user.is_authenticated:
            raise DetailedPermissionDenied(
                detail="Debe estar autenticado para realizar esta acción",
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        if view.action == 'create':
            if request.user.is_superuser:
                raise DetailedPermissionDenied(
                    detail="Los superusuarios no pueden crear perfiles de coleccionista."
                )

            if request.user.has_profile:
                raise DetailedPermissionDenied(
                    detail="Ya tienes un perfil creado. No puedes crear otro."
                )

            return True

        if view.action in ['list', 'count']:
            if not request.user.is_superuser:
                raise DetailedPermissionDenied(
                    "Sólo los  superusuarios pueden ejecutar esta acción")

            return True

        if view.action in ['me']:
            if not request.user.is_collector:
                raise DetailedPermissionDenied(
                    "Sólo los  coleccionistas pueden ejecutar esta acción")

            return True

        return True

    def has_object_permission(self, request, view, obj):

        if request.user.is_superuser:

            if request.method not in permissions.SAFE_METHODS:
                raise DetailedPermissionDenied(
                    code="Los superusuarios solo pueden ver perfiles, no modificarlos."
                )

            return True

        if obj.user != request.user:
            raise DetailedPermissionDenied(
                detail="Solo puedes acceder a tu propio perfil."
            )

        return True
