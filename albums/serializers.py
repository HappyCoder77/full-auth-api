from rest_framework import serializers
from editions.serializers import PackSerializer
from editions.serializers import StickerSerializer
from .models import Album, Page, Slot


class SlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slot
        fields = ("id", "number", "absolute_number", "image", "is_empty")


class PageSerializer(serializers.ModelSerializer):
    slots = SlotSerializer(many=True, read_only=True)
    is_full = serializers.BooleanField(read_only=True)
    prize_was_claimed = serializers.BooleanField(read_only=True)

    class Meta:
        model = Page
        fields = ("id", "number", "slots", "is_full", "prize_was_claimed")


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
                return f"{obj.image.url}"
            except:
                return None
        return None
