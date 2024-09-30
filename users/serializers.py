from rest_framework import serializers

from .models import RegionalManager, LocalManager

from djoser.serializers import UserSerializer as BaseUserSerializer


class UserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        fields = BaseUserSerializer.Meta.fields + ('is_superuser',)


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
