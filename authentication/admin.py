from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .forms import UserAccountChangeForm, UserAccountCreationForm
from .models import UserAccount


class UserAccountAdmin(UserAdmin):
    add_form = UserAccountCreationForm
    form = UserAccountChangeForm
    model = UserAccount
    list_display = ("email", 'id', "is_staff", "is_active",
                    "is_superuser", "is_collector", "is_regionalmanager", "is_localmanager", "is_sponsor", "is_dealer", )
    fieldsets = (
        ("Datos Personales", {
         "fields": ("email",)}),
        ("Permissions", {"fields": ("is_staff",
         "is_active",  "is_superuser", "groups", "user_permissions",)}),
        ("Dates", {"fields": ("last_login",)}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email", "password1", "password2", "is_staff", "is_active", "is_collector", "is_superuser"
            )
        }),
    )

    def is_regionalmanager(self, obj):
        return obj.is_regionalmanager

    is_regionalmanager.short_description = 'RM'
    is_regionalmanager.boolean = True

    def is_localmanager(self, obj):
        return obj.is_localmanager
    is_localmanager.short_description = 'LM'
    is_localmanager.boolean = True

    def is_sponsor(self, obj):
        return obj.is_sponsor
    is_sponsor.short_description = 'SP'
    is_sponsor.boolean = True

    def is_dealer(self, obj):
        return obj.is_dealer
    is_dealer.short_description = 'DL'
    is_dealer.boolean = True

    search_fields = ("email",)
    ordering = ("email",)


admin.site.register(UserAccount, UserAccountAdmin)
