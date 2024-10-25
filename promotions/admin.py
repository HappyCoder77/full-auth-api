from django.contrib import admin
from .models import Promotion


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'start_date', 'end_date',
                    'remaining_time', 'envelope_cost')
    ordering = ('-start_date',)
    exclude = ('end_date', )
    search_fields = ('name',)
