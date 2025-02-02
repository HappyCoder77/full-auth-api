from rest_framework.serializers import ModelSerializer

from .models import Collection, Coordinate, SurprisePrize


class CollectionSerializer(ModelSerializer):
    class Meta:
        model = Collection
        fields = ("name", "image")


class CoordinateSerializer(ModelSerializer):
    class Meta:
        model = Coordinate
        fields = ("id", "absolute_number", "image")


class SurprisePrizeSerializer(ModelSerializer):
    class Meta:
        model = SurprisePrize
        fields = ("description",)


from rest_framework import serializers
from .models import StandardPrize


class StandardPrizeSerializer(serializers.ModelSerializer):
    collection_name = serializers.CharField(source="collection.name", read_only=True)

    class Meta:
        model = StandardPrize
        fields = ["id", "collection", "collection_name", "page", "description"]
