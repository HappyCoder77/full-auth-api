from django.contrib import admin
from django.urls import path, include
from rest_framework.documentation import include_docs_urls
from rest_framework.schemas import get_schema_view
from rest_framework import permissions

# TODO: probar drf-espectacular lo sugiere la doc de drf.
API_TITLE = "Mis Barajitas API"
API_DESCRIPTION = 'backend de aplicacion web Mis Barajitas'
schema_view = get_schema_view(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version="1.0.0",
    public=True,
    permission_classes=(permissions.AllowAny,)
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('djoser.urls')),
    path('api/', include('users.urls')),
    path('api/', include('promotions.urls')),
    path('api/', include('albums.urls')),
    path('docs/', include_docs_urls(title=API_TITLE, description=API_DESCRIPTION)),
    path('schema/', schema_view)
]
