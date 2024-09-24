from django.contrib import admin
from .models import UserAccount, RegionalManager


class RegionalManagerAdmin(admin.ModelAdmin):
    fields = ['email', 'first_name', 'middle_name', 'first_last_name',
              'second_last_name', 'sex', 'birthdate', 'created_by']


admin.site.register(UserAccount)
admin.site.register(RegionalManager, RegionalManagerAdmin)
