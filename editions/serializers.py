from rest_framework.serializers import ModelSerializer, SerializerMethodField, CharField

from collection_manager.serializers import CollectionSerializer
from collection_manager.serializers import CoordinateSerializer, SurprisePrizeSerializer
from promotions.serializers import PromotionSerializer
from .models import Edition, Pack, Sticker, StickerPrize


class EditionSerializer(ModelSerializer):
    promotion = PromotionSerializer(read_only=True)
    collection = CollectionSerializer(read_only=True)

    class Meta:
        model = Edition
        fields = ("id", "promotion", "collection")


class StickerPrizeSerializer(ModelSerializer):
    prize = SurprisePrizeSerializer(read_only=True)
    status_display = CharField(source="get_status_display")

    class Meta:
        model = StickerPrize
        fields = [
            "id",
            "prize",
            "claimed",
            "claimed_date",
            "claimed_by",
            "status",
            "status_display",
        ]


class StickerSerializer(ModelSerializer):
    coordinate = CoordinateSerializer(read_only=True)
    prize = StickerPrizeSerializer(read_only=True)
    has_prize_discovered = SerializerMethodField()

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
            "has_prize_discovered",
        )

    def get_has_prize_discovered(self, obj):
        return obj.has_prize_discovered()


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
