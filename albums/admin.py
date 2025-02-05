from django.contrib import admin
from .models import Album, Page, Slot, PagePrize


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    model = Album
    list_display = ("id", "collector", "edition", "image")


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    model = Page
    list_display = ("id", "album_id", "number")


@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    model = Slot


@admin.register(PagePrize)
class PagePrizeAdmin(admin.ModelAdmin):
    model = PagePrize
    list_display = (
        "page",
        "prize",
        "collector",
        "claimed",
        "claimed_by",
        "claimed_date",
        "status",
    )

    def collector(self, obj):
        return obj.page.album.collector

    collector.short_description = "Collector"
