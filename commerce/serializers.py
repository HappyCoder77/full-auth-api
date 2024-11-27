from rest_framework import serializers
from .models import Order, Box
from django.contrib.auth import get_user_model


class BoxSerializer(serializers.ModelSerializer):
    class Meta:
        model = Box
        fields = ['id', 'edition']


class OrderSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(
        read_only=True, max_digits=10, decimal_places=2)

    class Meta:
        model = Order
        fields = ['id', 'dealer', 'date',
                  'edition', 'box', 'pack_cost', 'amount']
        read_only_fields = ['date', 'pack_cost', 'dealer', 'box']
