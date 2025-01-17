from django.urls import path
from .views import UserAlbumListRetrieveView, UserAlbumCreateView, AlbumDetailView


urlpatterns = [
    path("user-albums/", UserAlbumListRetrieveView.as_view(), name="user-albums-list"),
    path(
        "user-albums/retrieve/<int:edition_id>/",
        UserAlbumListRetrieveView.as_view(),
        name="user-albums-retrieve",
    ),
    path(
        "user-albums/create/", UserAlbumCreateView.as_view(), name="user-albums-create"
    ),
    path("albums/<int:pk>/", AlbumDetailView.as_view(), name="album-detail"),
]
