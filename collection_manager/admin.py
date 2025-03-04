from django.contrib import admin

from .models import (
    OldCollection,
    Coordinate,
    StandardPrize,
    SurprisePrize,
    Collection,
    Theme,
)


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "image")


@admin.register(OldCollection)
class OldCollectionAdmin(admin.ModelAdmin):
    list_display = ("id", "name")


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ("id", "theme", "promotion")


@admin.register(Coordinate)
class CoordinateAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "collection",
        "page",
        "slot_number",
        "absolute_number",
        "ordinal",
        "rarity_factor",
        "image",
    )
    ordering = (
        "id",
        "collection",
    )
    list_filter = ("page", "slot_number", "rarity_factor", "collection")
    search_fields = ("rarity_factor",)

    def has_add_permission(self, request):
        return False


@admin.register(StandardPrize)
class StandardPrizeAdmin(admin.ModelAdmin):
    list_display = ("collection", "page", "description")
    ordering = ("collection",)


@admin.register(SurprisePrize)
class SurprisePrizeAdmin(admin.ModelAdmin):
    list_display = ("collection", "number", "description")
    ordering = ("collection",)
