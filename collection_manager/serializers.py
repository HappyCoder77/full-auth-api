from rest_framework.serializers import ModelSerializer, PrimaryKeyRelatedField

from promotions.serializers import PromotionSerializer
from .models import Collection, Coordinate, SurprisePrize, Theme


class ThemeSerializer(ModelSerializer):
    class Meta:
        model = Theme
        fields = ("name", "image")


class CollectionSerializer(ModelSerializer):
    promotion = PromotionSerializer(read_only=True)
    theme = ThemeSerializer(read_only=True)

    class Meta:
        model = Collection
        fields = ("id", "promotion", "theme")


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
    collection_name = serializers.CharField(
        source="collection.theme.name", read_only=True
    )

    class Meta:
        model = StandardPrize
        fields = ["id", "collection", "collection_name", "page", "description"]
