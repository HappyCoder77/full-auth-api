from django.contrib import admin
from .models import (Promotion, Collection, Coordinate,
                     StandardPrize, SurprisePrize, Edition, Pack, Sticker, Box)


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'start_date', 'end_date',
                    'remaining_time', 'pack_cost')
    ordering = ('-start_date',)
    exclude = ('end_date', )
    search_fields = ('name',)


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(Coordinate)
class CoordenadaAdmin(admin.ModelAdmin):
    list_display = ('id', 'collection', 'page', 'slot',
                    'ordinal', 'number', 'rarity_factor')
    ordering = ('id', 'collection',)
    list_filter = ('page', 'slot', 'rarity_factor')
    search_fields = ('rarity_factor',)

    def has_add_permission(self, request):
        return False


@admin.register(StandardPrize)
class StandardPrizeAdmin(admin.ModelAdmin):
    list_display = ('collection', 'page', 'description')
    ordering = ('collection',)


@admin.register(SurprisePrize)
class SurprisePrizeAdmin(admin.ModelAdmin):
    list_display = ('collection', 'number', 'description')
    ordering = ('collection',)


@admin.register(Edition)
class EditionAdmin(admin.ModelAdmin):
    list_display = ('id', 'promotion', 'collection', 'circulation')
    list_filter = ('promotion', 'collection')
    exclude = ('promotion',)


@admin.register(Pack)
class PackAdmin(admin.ModelAdmin):
    list_display = ('id', 'box', 'edition', 'ordinal',)
    ordering = ('id',)
    list_filter = ('box', 'box__edition')
    search_fields = ('box__edition__name',)

    def has_add_permission(self, request):
        return False


@admin.register(Sticker)
class StickerAdmin(admin.ModelAdmin):
    list_display = ('id', 'number', 'ordinal',
                    'rarity', 'pack', 'collector')
    ordering = ('id',)
    list_filter = ('pack__box', 'coordinate__rarity_factor')

    def has_add_permission(self, request):
        return False


@admin.register(Box)
class BoxAdmin(admin.ModelAdmin):
    list_display = ('edition', 'id', 'ordinal')
    ordering = ('id',)
    list_filter = ('edition', 'ordinal')

    def has_add_permission(self, request):
        return False
