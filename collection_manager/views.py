from rest_framework.generics import ListAPIView
from albums.permissions import IsAuthenticatedCollector
from .models import Collection
from .serializers import CollectionSerializer


class CurrentCollectionListView(ListAPIView):
    serializer_class = CollectionSerializer
    http_method_names = ["get"]
    permission_classes = [IsAuthenticatedCollector]

    def get_queryset(self):
        return Collection.objects.get_current_list() or []
