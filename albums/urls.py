from django.urls import path
from .views import (
    UserAlbumListRetrieveView,
    UserAlbumCreateView,
    AlbumDetailView,
    OpenPackView,
    PlaceStickerView,
    DiscoverStickerPrizeView,
    CreatePagePrizeView,
    PagePrizeListAPIView,
    RescuePoolView,
)


urlpatterns = [
    path("user-albums/", UserAlbumListRetrieveView.as_view(), name="user-albums-list"),
    path(
        "user-albums/retrieve/<int:collection_id>/",
        UserAlbumListRetrieveView.as_view(),
        name="user-albums-retrieve",
    ),
    path(
        "user-albums/create/", UserAlbumCreateView.as_view(), name="user-albums-create"
    ),
    path("albums/<int:pk>/", AlbumDetailView.as_view(), name="album-detail"),
    path("packs/<int:pk>/open/", OpenPackView.as_view(), name="open-pack"),
    path(
        "stickers/<int:sticker_id>/place/",
        PlaceStickerView.as_view(),
        name="place-sticker",
    ),
    path(
        "stickers/<int:sticker_id>/discover-prize/",
        DiscoverStickerPrizeView.as_view(),
        name="discover-prize",
    ),
    path(
        "pages/<int:page_id>/create-prize/",
        CreatePagePrizeView.as_view(),
        name="create-page-prize",
    ),
    path(
        "prizes/page-prize/list/",
        PagePrizeListAPIView.as_view(),
        name="create-page-prize",
    ),
    path(
        "stickers/rescue-pool/",
        RescuePoolView.as_view(),
        name="rescue-pool",
    ),
]
