from django.contrib import admin
from .models import Promotion, Collection, Coordinate, StandardPrize, SurprisePrize


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'start_date', 'end_date',
                    'remaining_time', 'envelope_cost')
    ordering = ('-start_date',)
    exclude = ('end_date', )
    search_fields = ('name',)


@admin.register(Collection)
class ColeccionAdmin(admin.ModelAdmin):
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


# @admin.register(StandardPrize)
# class StandardPrizeAdmin(admin.ModelAdmin):
#     list_display = ('collection', 'page', 'description')
#     ordering = ('collection',)


# @admin.register(SurprisePrize)
# class SurprisePrizeAdmin(admin.ModelAdmin):
#     list_display = ('collection', 'number', 'description')
#     ordering = ('collection',)
