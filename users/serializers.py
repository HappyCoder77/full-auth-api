from rest_framework import serializers
from editions.serializers import StickerPrizeSerializer
from .models import (
    RegionalManager,
    LocalManager,
    Sponsor,
    Dealer,
    BaseProfile,
    Collector,
)


class RegionalManagerSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegionalManager
        fields = [
            "id",
            "user",
            "first_name",
            "middle_name",
            "last_name",
            "second_last_name",
            "gender",
            "birthdate",
            "email",
            "created_by",
        ]

        extra_kwargs = {"user": {"write_only": True}}


class LocalManagerSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocalManager
        fields = [
            "id",
            "user",
            "first_name",
            "middle_name",
            "last_name",
            "second_last_name",
            "gender",
            "birthdate",
            "email",
            "created_by",
        ]

        extra_kwargs = {"user": {"write_only": True}}


class SponsorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sponsor
        fields = [
            "id",
            "user",
            "first_name",
            "middle_name",
            "last_name",
            "second_last_name",
            "gender",
            "birthdate",
            "email",
            "created_by",
        ]

        extra_kwargs = {"user": {"write_only": True}}


class DealerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dealer
        fields = [
            "id",
            "user",
            "first_name",
            "middle_name",
            "last_name",
            "second_last_name",
            "gender",
            "birthdate",
            "email",
            "created_by",
        ]

        extra_kwargs = {"user": {"write_only": True}}


class BaseProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseProfile
        fields = [
            "id",
            "user",
            "first_name",
            "middle_name",
            "last_name",
            "second_last_name",
            "gender",
            "birthdate",
            "email",
        ]

        extra_kwargs = {"user": {"write_only": True}}


class CollectorSerializer(serializers.ModelSerializer):
    unclaimed_surprise_prizes = StickerPrizeSerializer(many=True, read_only=True)

    class Meta:
        model = Collector
        fields = [
            "id",
            "user",
            "first_name",
            "middle_name",
            "last_name",
            "second_last_name",
            "gender",
            "birthdate",
            "email",
            "unclaimed_surprise_prizes",
        ]

        extra_kwargs = {"user": {"write_only": True}}
