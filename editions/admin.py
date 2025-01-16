from django.contrib import admin

from .models import Edition, Box, Pack, Sticker


@admin.register(Edition)
class EditionAdmin(admin.ModelAdmin):
    list_display = ("id", "promotion", "collection", "circulation")
    list_filter = ("promotion", "collection")
    exclude = ("promotion",)


@admin.register(Box)
class BoxAdmin(admin.ModelAdmin):
    list_display = ("edition", "id", "ordinal")
    ordering = ("id",)
    list_filter = ("edition", "ordinal")

    def has_add_permission(self, request):
        return False


@admin.register(Pack)
class PackAdmin(admin.ModelAdmin):
    list_display = ("id", "box", "edition", "ordinal", "sale")
    ordering = ("id",)
    list_filter = ("box", "box__edition", "sale__sale")
    search_fields = ("box__edition__name",)

    def has_add_permission(self, request):
        return False


@admin.register(Sticker)
class StickerAdmin(admin.ModelAdmin):
    list_display = ("id", "number", "ordinal", "rarity", "pack", "collector")
    ordering = ("id",)
    list_filter = ("pack__box", "coordinate__rarity_factor")

    def has_add_permission(self, request):
        return False
