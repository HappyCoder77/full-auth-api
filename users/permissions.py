from rest_framework import permissions


class IsNotAuthenticated(permissions.BasePermission):
    """
    Permite el acceso solo a usuarios no autenticados.
    """
    message = "Lo siento, esta vista solo está disponible para usuarios no autenticados."

    def has_permission(self, request, view):
        return not request.user.is_authenticated


class IsSuperUser(permissions.BasePermission):
    """
    Permite el acceso solo a los superusuarios.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_superuser
