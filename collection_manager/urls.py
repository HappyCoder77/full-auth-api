from django.urls import path
from .views import CurrentCollectionListView, CollectionDetailView

urlpatterns = [
    path(
        "collections/current/",
        CurrentCollectionListView.as_view(),
        name="current-collections",
    ),
    path(
        "collections/<int:pk>/",
        CollectionDetailView.as_view(),
        name="collection-detail",
    ),
]
