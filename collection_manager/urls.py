from django.urls import path
from .views import CurrentCollectionListView

urlpatterns = [
    path(
        "collections/current/",
        CurrentCollectionListView.as_view(),
        name="current-collections",
    ),
]
