from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from .models import Order, Payment, DealerBalance, Box
from .forms import OrderForm
from editions.models import Edition


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    model = Order
    list_display = ("id", "date", "dealer", "box", "amount")
    form = OrderForm

    class Media:
        js = ("commerce/admin/order_form.js",)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "boxes/<int:edition_id>/",
                self.admin_site.admin_view(self.get_boxes),
                name="get_boxes",
            ),
        ]
        return custom_urls + urls

    def get_boxes(self, request, edition_id):
        boxes = Box.objects.filter(edition_id=edition_id).values("id", "ordinal")
        return JsonResponse(list(boxes), safe=False)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    model = Payment
    list_display = (
        "id",
        "status",
        "dealer",
        "payment_date",
        "date",
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
        "end_date",
        "dealer",
        "promotion",
        "initial_balance",
        "created_at",
        "orders_total",
        "payments_total",
        "current_balance",
    )
