from rest_framework import serializers
from editions.serializers import PackSerializer
from editions.serializers import StickerSerializer
from collection_manager.serializers import StandardPrizeSerializer
from .models import Album, Page, Slot, PagePrize
from django.conf import settings


class SlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slot
        fields = ("id", "number", "absolute_number", "image", "is_empty")


class PagePrizeSerializer(serializers.ModelSerializer):
    prize = StandardPrizeSerializer(read_only=True)
    status_display = serializers.CharField(source="get_status_display")

    class Meta:
        model = PagePrize
        fields = (
            "id",
            "page",
            "prize",
            "claimed_by",
            "claimed_date",
            "status",
            "status_display",
        )


class PageSerializer(serializers.ModelSerializer):
    page_prize = PagePrizeSerializer(read_only=True)
    slots = SlotSerializer(many=True, read_only=True)
    is_full = serializers.BooleanField(read_only=True)
    prize_was_claimed = serializers.BooleanField(read_only=True)

    class Meta:
        model = Page
        fields = ("id", "page_prize", "number", "slots", "is_full", "prize_was_claimed")


class AlbumSerializer(serializers.ModelSerializer):
    pages = PageSerializer(many=True, read_only=True)
    collector = serializers.PrimaryKeyRelatedField(read_only=True)
    pack_inbox = PackSerializer(many=True, read_only=True)
    stickers_on_the_board = StickerSerializer(many=True, read_only=True)
    prized_stickers = StickerSerializer(many=True, read_only=True)
    image = serializers.SerializerMethodField()

    class Meta:
        model = Album
        fields = (
            "id",
            "edition",
            "image",
            "collector",
            "pages",
            "pack_inbox",
            "stickers_on_the_board",
            "prized_stickers",
        )


def get_image(self, obj):
    if obj.image:
        try:
            if settings.DEVELOPMENT_MODE:
                return obj.image.url
            return f"https://spaces.misbarajitas.com{obj.image.url}"
        except:
            return None
    return None
