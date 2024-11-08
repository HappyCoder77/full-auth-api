from rest_framework import status
from rest_framework.exceptions import APIException


class DetailedPermissionDenied(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "No tienes permiso para ejecutar esta acción"
    default_code = "permission denied"

    def __init__(self, detail=None, code=None, status_code=None):
        super().__init__(detail, code)

        if status_code is not None:
            self.status_code = status_code
