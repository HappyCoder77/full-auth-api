from django.utils import timezone
from rest_framework import serializers
from .models import Order, Box, Payment, MobilePayment
from django.contrib.auth import get_user_model


class BoxSerializer(serializers.ModelSerializer):
    class Meta:
        model = Box
        fields = ["id", "edition"]


class OrderSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)

    class Meta:
        model = Order
        fields = ["id", "dealer", "date", "edition", "box", "pack_cost", "amount"]
        read_only_fields = ["date", "pack_cost", "dealer", "box"]


class PaymentSerializer(serializers.ModelSerializer):
    dealer_email = serializers.EmailField(source="dealer.email", read_only=True)
    bank_name = serializers.CharField(source="get_bank_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "status",
            "dealer",
            "dealer_email",
            "date",
            "payment_date",
            "bank",
            "bank_name",
            "amount",
            "reference",
            "id_number",
            "capture",
            "payment_type",
            "status_display",
        ]
        read_only_fields = [
            "id",
            "dealer",
            "date",
            "dealer_email",
            "bank_name",
            "status_display",
        ]

    def validate_payment_date(self, value):
        if value > timezone.now().date():
            raise serializers.ValidationError(
                "La fecha de pago no puede ser en el futuro."
            )
        return value

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("El monto debe ser mayor que cero.")
        return value


class MobilePaymentSerializer(PaymentSerializer):
    class Meta(PaymentSerializer.Meta):
        model = MobilePayment
        fields = PaymentSerializer.Meta.fields + ["phone_code", "phone_number"]

    def validate(self, data):
        data = super().validate(data)
        if data.get("payment_type") != "mobile":
            raise serializers.ValidationError(
                "El tipo de pago debe ser 'mobile' para pagos móviles."
            )
        return data
