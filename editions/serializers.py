from rest_framework.serializers import ModelSerializer
from .models import Edition


class EditionSerializer(ModelSerializer):
    class Meta:
        model = Edition
        fields = ('promotion', 'collection')
