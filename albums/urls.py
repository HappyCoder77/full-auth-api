from django.urls import path
from .views import UserAlbumListRetrieveView, UserAlbumCreateView


urlpatterns = [
    path('user-albums/', UserAlbumListRetrieveView.as_view(),
         name='user-albums-list'),
    path('user-albums/retrieve/<int:edition_id>/',
         UserAlbumListRetrieveView.as_view(), name='user-albums-retrieve'),
    path('user-albums/create/',
         UserAlbumCreateView.as_view(), name='user-albums-create')
]
