from rest_framework import serializers
from editions.serializers import PackSerializer
from editions.serializers import StickerSerializer
from .models import Album, Page, Slot


class SlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slot
        fields = ("number", "absolute_number", "image")


class PageSerializer(serializers.ModelSerializer):
    slots = SlotSerializer(many=True, read_only=True)

    class Meta:
        model = Page
        fields = ("id", "number", "slots")


class AlbumSerializer(serializers.ModelSerializer):
    pages = PageSerializer(many=True, read_only=True)
    collector = serializers.PrimaryKeyRelatedField(read_only=True)
    pack_inbox = PackSerializer(many=True, read_only=True)
    stickers_on_the_board = StickerSerializer(many=True, read_only=True)

    class Meta:
        model = Album
        fields = (
            "id",
            "edition",
            "collector",
            "pages",
            "pack_inbox",
            "stickers_on_the_board",
        )
