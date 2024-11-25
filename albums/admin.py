from django.contrib import admin
from .models import Album, Page, Slot


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    model = Album


@admin.register(Page)
class AlbumAdmin(admin.ModelAdmin):
    model = Page


@admin.register(Slot)
class AlbumAdmin(admin.ModelAdmin):
    model = Slot
