from django.contrib import admin
from .models import Promotion


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "id",
        "start_date",
        "end_date",
        "remaining_time",
        "pack_cost",
        "balances_created",
    )
    ordering = ("-start_date",)
    exclude = ("end_date",)
    search_fields = ("name",)
