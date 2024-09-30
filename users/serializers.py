from rest_framework import serializers

from .models import RegionalManager, LocalManager


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
