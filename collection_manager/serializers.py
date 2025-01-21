from rest_framework.serializers import ModelSerializer

from .models import Collection, Coordinate


class CollectionSerializer(ModelSerializer):
    class Meta:
        model = Collection
        fields = ("name", "image")


class CoordinateSerializer(ModelSerializer):
    class Meta:
        model = Coordinate
        fields = ("id", "absolute_number", "image")
