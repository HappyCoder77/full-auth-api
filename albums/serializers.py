from rest_framework import serializers
from .models import Album, Page, Slot


class SlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slot
        fields = ('number', 'absolute_number')


class PageSerializer(serializers.ModelSerializer):
    slots = SlotSerializer(many=True, read_only=True)

    class Meta:
        model = Page
        fields = ('id', 'number', 'slots')


class AlbumSerializer(serializers.ModelSerializer):
    pages = PageSerializer(many=True, read_only=True)
    collector = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Album
        fields = ('id', 'edition', 'collector', 'pages')
