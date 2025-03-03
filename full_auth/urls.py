from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include


from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)


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
    path("plate/", include("django_spaghetti.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
