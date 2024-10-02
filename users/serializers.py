from rest_framework import serializers

from .models import RegionalManager, LocalManager, Sponsor

from djoser.serializers import UserSerializer as BaseUserSerializer


class UserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        fields = BaseUserSerializer.Meta.fields + \
            ('is_superuser', 'is_regionalmanager', "is_localmanager", "is_sponsor")

    def get_is_regionalmanager(self, obj):
        return obj.is_regionalmanager()

    def get_is_localmanager(self, obj):
        return obj.is_localmanager()

    def get_is_sponsor(self, obj):
        return obj.is_sponsor()


class RegionalManagerSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegionalManager
        fields = ['id', 'user', 'first_name', 'middle_name', 'last_name',
                  'second_last_name', 'gender', 'birthdate', 'email', 'created_by']

        extra_kwargs = {
            "user": {"write_only": True}
        }


class LocalManagerSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocalManager
        fields = ['id', 'user', 'first_name', 'middle_name', 'last_name',
                  'second_last_name', 'gender', 'birthdate', 'email', 'created_by']

        extra_kwargs = {
            "user": {"write_only": True}
        }


class SponsorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sponsor
        fields = ['id', 'user', 'first_name', 'middle_name', 'last_name',
                  'second_last_name', 'gender', 'birthdate', 'email', 'created_by']

        extra_kwargs = {
            "user": {"write_only": True}
        }
