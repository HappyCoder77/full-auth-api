from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

# from rest_framework.documentation import include_docs_urls
# from rest_framework.schemas import get_schema_view
# from rest_framework import permissions
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

# TODO: probar drf-espectacular lo sugiere la doc de drf.
# API_TITLE = "Mis Barajitas API"
# API_DESCRIPTION = 'backend de aplicacion web Mis Barajitas'
# schema_view = get_schema_view(
#     title=API_TITLE,
#     description=API_DESCRIPTION,
#     version="1.0.0",
#     public=True,
#     permission_classes=(permissions.AllowAny,)
# )

urlpatterns = [
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("admin/", admin.site.urls),
    path("api/", include("albums.urls")),
    path("api/", include("authentication.urls")),
    path("api/", include("promotions.urls")),
    path("api/", include("editions.urls")),
    path("api/", include("users.urls")),
    path("api/", include("commerce.urls")),
    # API Schema documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
