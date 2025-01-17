from rest_framework.serializers import ModelSerializer

from collection_manager.serializers import CollectionSerializer
from promotions.serializers import PromotionSerializer
from .models import Edition, Pack


class EditionSerializer(ModelSerializer):
    promotion = PromotionSerializer(read_only=True)
    collection = CollectionSerializer(read_only=True)

    class Meta:
        model = Edition
        fields = ("id", "promotion", "collection")


class PackSerializer(ModelSerializer):
    class Meta:
        model = Pack
        fields = ("id", "is_open", "collector")
