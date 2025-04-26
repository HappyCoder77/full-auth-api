from django.contrib import admin

from .models import (
    Coordinate,
    StandardPrize,
    SurprisePrize,
    Collection,
    Theme,
    AlbumTemplate,
)


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display = ("__str__", "id", "name", "image")


@admin.register(AlbumTemplate)
class AlbumTemplateAdmin(admin.ModelAdmin):
    list_display = ("__str__", "id", "name", "image")
    fields = ("name", "image")


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ("__str__", "id", "album_template", "promotion")
    fields = ("album_template",)


@admin.register(Coordinate)
class CoordinateAdmin(admin.ModelAdmin):
    list_display = (
        "absolute_number",
        "id",
        "template",
        "page",
        "slot_number",
        "ordinal",
        "rarity_factor",
        "image",
    )
    ordering = (
        "id",
        "template",
    )
    list_filter = ("page", "slot_number", "rarity_factor", "template")
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
