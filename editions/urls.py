from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import EditionViewSet, RescueStickerView

router = DefaultRouter()

router.register("edition", EditionViewSet, basename="edition")

urlpatterns = [
    *router.urls,
    path(
        "stickers/<int:sticker_id>/rescue/",
        RescueStickerView.as_view(),
        name="rescue-sticker",
    ),
]
