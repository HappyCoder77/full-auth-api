from django.contrib import admin
from django.utils.html import format_html
from .models import Edition, Box, Pack, Sticker, StickerPrize


@admin.register(Edition)
class EditionAdmin(admin.ModelAdmin):
    list_display = (
        "collection",
        "id",
        "circulation",
        "distribution_status",
    )
    readonly_fields = ["distribution_stats", "validation_details"]
    list_filter = ("collection",)
    search_fields = ["collection__name", "promotion__name"]
    fieldsets = (
        (None, {"fields": ("collection", "circulation")}),
        (
            "Distribution Information",
            {
                "fields": ("distribution_stats", "validation_details"),
                "classes": ("wide",),
            },
        ),
    )

    def distribution_status(self, obj):
        is_valid, results = obj.validate_distribution()
        if is_valid:
            return format_html('<span style="color: green;">✓ Valid</span>')
        return format_html('<span style="color: red;">✗ Invalid</span>')

    def distribution_stats(self, obj):
        stats = obj.get_distribution_stats()
        return format_html(
            """
            <div style="padding: 15px; border: 2px solid #ddd; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <p style="color: white; margin: 5px 0;"><strong>Total Boxes:</strong> <span style="color: green">{0}</span></p>
                <p style="color: white; margin: 5px 0;"><strong>Total Packs:</strong> <span style="color: green">{1}</span></p>
                <p style="color: white; margin: 5px 0;"><strong>Prize Packs:</strong> <span style="color: green">{2}</span></p>
                <p style="color: white; margin: 5px 0;"><strong>Standard Packs:</strong> <span style="color: green">{3}</span></p>
            </div>
            """,
            stats["total_boxes"],
            stats["total_packs"],
            stats["prize_packs"],
            stats["standard_packs"],
        )

    def validation_details(self, obj):
        _, results = obj.validate_distribution()
        html = ['<div style="padding: 10px;">']
        for check, passed in results.items():
            status = "✓" if passed else "✗"
            color = "green" if passed else "red"
            html.append(f'<p style="color: {color}">{status} {check}</p>')
        html.append("</div>")
        return format_html("".join(html))

    distribution_status.short_description = "Status"
    distribution_stats.short_description = "Distribution Statistics"
    validation_details.short_description = "Validation Details"


@admin.register(Box)
class BoxAdmin(admin.ModelAdmin):
    list_display = ("edition", "edition_id", "id", "ordinal")
    ordering = ("id",)
    list_filter = ("edition", "ordinal")

    def has_add_permission(self, request):
        return False


@admin.register(Pack)
class PackAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "box",
        "edition",
        "ordinal",
        "sale",
        "collector",
        "is_open",
    )
    list_select_related = (
        "box",
        "box__edition",
        "collector",
        "sale",
    )
    ordering = ("id",)
    list_filter = ("box", "box__edition", "sale__sale", "collector", "is_open")
    search_fields = ("box__edition__name",)

    def has_add_permission(self, request):
        return False


@admin.register(Sticker)
class StickerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "number",
        "ordinal",
        "rarity",
        "pack",
        "collector",
        "on_the_board",
        "pack__box__edition",
    )
    ordering = ("id",)
    list_filter = (
        "pack__box",
        "coordinate__rarity_factor",
        "on_the_board",
        "collector",
        "pack__box__edition",
    )

    def has_add_permission(self, request):
        return False


@admin.register(StickerPrize)
class StickerPrizeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "sticker",
        "prize",
        "claimed",
        "claimed_date",
        "claimed_by",
        "status",
    )
