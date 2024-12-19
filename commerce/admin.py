from django.contrib import admin
from .models import Order, Payment, DealerBalance


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    model = Order
    list_display = ("id", "date", "dealer", "box", "amount")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    model = Payment
    list_display = (
        "id",
        "status",
        "dealer",
        "date",
        "payment_date",
        "bank",
        "amount",
        "reference",
        "id_number",
        "capture",
        "payment_type",
    )


@admin.register(DealerBalance)
class DealerBalanceAdmin(admin.ModelAdmin):
    model = DealerBalance
    list_display = (
        "id",
        "start_date",
        "dealer",
        "promotion",
        "initial_balance",
        "end_date",
        "created_at",
        "orders_total",
        "payments_total",
        "current_balance",
    )
