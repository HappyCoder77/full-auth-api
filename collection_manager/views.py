from rest_framework.generics import ListAPIView, RetrieveAPIView
from albums.permissions import IsAuthenticatedCollector
from commerce.permissions import IsAuthenticatedDealer
from .models import Collection
from .serializers import CollectionSerializer


class CurrentCollectionListView(ListAPIView):
    serializer_class = CollectionSerializer
    http_method_names = ["get"]
    permission_classes = [IsAuthenticatedCollector]

    def get_queryset(self):
        return Collection.objects.get_current_list() or []


class CollectionDetailView(RetrieveAPIView):
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer
    http_method_names = ["get"]
    permission_classes = [IsAuthenticatedDealer]
