from rest_framework.serializers import ModelSerializer

from collection_manager.serializers import CollectionSerializer
from collection_manager.serializers import CoordinateSerializer
from promotions.serializers import PromotionSerializer
from .models import Edition, Pack, Sticker, StickerPrize


class EditionSerializer(ModelSerializer):
    promotion = PromotionSerializer(read_only=True)
    collection = CollectionSerializer(read_only=True)

    class Meta:
        model = Edition
        fields = ("id", "promotion", "collection")


class StickerPrizeSerializer(ModelSerializer):
    class Meta:
        model = StickerPrize
        fields = ["id", "prize", "claimed", "claimed_date"]


class StickerSerializer(ModelSerializer):
    coordinate = CoordinateSerializer(read_only=True)
    prize = StickerPrizeSerializer(read_only=True)

    class Meta:
        model = Sticker
        fields = (
            "id",
            "ordinal",
            "number",
            "on_the_board",
            "is_repeated",
            "coordinate",
            "prize",
        )


class PackSerializer(ModelSerializer):
    stickers = StickerSerializer(many=True, read_only=True)

    class Meta:
        model = Pack
        fields = (
            "id",
            "is_open",
            "collector",
            "stickers",
        )
