from django.utils import timezone
from rest_framework import serializers
from .models import Order, Box, Payment, MobilePayment, DealerBalance, Pack, Sale
from collection_manager.models import Collection
from django.contrib.auth import get_user_model

User = get_user_model()


class BoxSerializer(serializers.ModelSerializer):
    class Meta:
        model = Box
        fields = ["id", "edition"]


class OrderSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)

    class Meta:
        model = Order
        fields = ["id", "dealer", "date", "collection", "box", "pack_cost", "amount"]
        read_only_fields = ["date", "pack_cost", "dealer", "box"]


class PaymentSerializer(serializers.ModelSerializer):
    dealer_email = serializers.EmailField(source="dealer.email", read_only=True)
    bank_name = serializers.CharField(source="get_bank_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    payment_type_display = serializers.CharField(
        source="get_payment_type_display", read_only=True
    )

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
            "payment_type_display",
            "status_display",
        ]
        read_only_fields = [
            "id",
            "dealer",
            "date",
            "dealer_email",
            "bank_name",
            "status_display",
            "payment_type_display",
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


class DealerBalanceSerializer(serializers.ModelSerializer):
    payments_total = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    orders_total = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    current_balance = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = DealerBalance
        fields = [
            "dealer",
            "promotion",
            "initial_balance",
            "start_date",
            "end_date",
            "payments_total",
            "orders_total",
            "current_balance",
            "created_at",
            "updated_at",
        ]


class SaleSerializer(serializers.ModelSerializer):
    date = serializers.DateField(read_only=True)
    dealer = serializers.PrimaryKeyRelatedField(read_only=True)
    dealer_name = serializers.CharField(
        source="dealer.baseprofile.get_full_name", read_only=True
    )
    collector = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=True
    )
    collector_name = serializers.CharField(
        source="collector.baseprofile.get_full_name", read_only=True
    )
    collection = serializers.PrimaryKeyRelatedField(
        queryset=Collection.objects.all(), required=True
    )
    collection_name = serializers.CharField(
        source="collection.album_template.name", read_only=True
    )

    class Meta:
        model = Sale
        fields = [
            "id",
            "date",
            "collection",
            "collection_name",
            "dealer",
            "dealer_name",
            "collector",
            "collector_name",
            "quantity",
        ]

    def validate(self, data):
        dealer = self.context["request"].user
        available_packs = (
            Pack.objects.filter(
                sale__isnull=True,
                box__edition__collection=data["collection"],
                box__order__dealer=dealer,
            )
            .order_by("ordinal")
            .count()
        )

        if available_packs < data["quantity"]:
            raise serializers.ValidationError(
                f"Inventario insuficiente: quedan {available_packs} packs disponibles"
            )
        return data
