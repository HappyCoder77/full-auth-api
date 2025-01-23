from django.contrib import admin
from .models import Album, Page, Slot


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    model = Album
    list_display = ("id", "collector", "edition", "image")


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    model = Page


@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    model = Slot
