from django.contrib import admin


from .models import (
    BaseProfile,
    RegionalManager,
    LocalManager,
    Sponsor,
    Dealer,
    Collector,
)


class RegionalManagerAdmin(admin.ModelAdmin):
    fields = [
        "user",
        "email",
        "first_name",
        "middle_name",
        "last_name",
        "second_last_name",
        "gender",
        "birthdate",
        "created_by",
    ]
    readonly_fields = ["user", "created_by"]

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # Solo para nuevos registros
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class BaseProfileAdmin(admin.ModelAdmin):
    fields = [
        "user",
        "email",
        "first_name",
        "middle_name",
        "last_name",
        "second_last_name",
        "gender",
        "birthdate",
    ]


class LocalManagerAdmin(admin.ModelAdmin):
    fields = [
        "user",
        "email",
        "first_name",
        "middle_name",
        "last_name",
        "second_last_name",
        "gender",
        "birthdate",
        "created_by",
    ]
    readonly_fields = ["user", "created_by"]

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # Solo para nuevos registros
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class SponsorAdmin(admin.ModelAdmin):
    fields = [
        "user",
        "email",
        "first_name",
        "middle_name",
        "last_name",
        "second_last_name",
        "gender",
        "birthdate",
        "created_by",
    ]
    readonly_fields = ["user", "created_by"]

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # Solo para nuevos registros
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class DealerAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "user",
        "id",
        "first_name",
        "middle_name",
        "last_name",
        "second_last_name",
        "gender",
        "birthdate",
        "created_by",
    )
    readonly_fields = ("id",)
    readonly_fields = ["user", "created_by"]

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # Solo para nuevos registros
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class CollectorAdmin(admin.ModelAdmin):
    fields = [
        "user",
        "email",
        "first_name",
        "middle_name",
        "last_name",
        "second_last_name",
        "gender",
        "birthdate",
    ]


admin.site.register(RegionalManager, RegionalManagerAdmin)
admin.site.register(LocalManager, LocalManagerAdmin)
admin.site.register(Sponsor, SponsorAdmin)
admin.site.register(Dealer, DealerAdmin)
admin.site.register(BaseProfile, BaseProfileAdmin)
admin.site.register(Collector, CollectorAdmin)
