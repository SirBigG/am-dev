from django.contrib import admin

from .models import Publication, PublicationStatusEvent


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ("topic", "author", "status", "kind", "published_at")
    list_filter = ("status", "kind", "is_featured")
    search_fields = ("topic__title", "excerpt", "author__username")
    readonly_fields = ("body_html", "created_at", "updated_at", "submitted_at", "published_at")


@admin.register(PublicationStatusEvent)
class PublicationStatusEventAdmin(admin.ModelAdmin):
    list_display = ("publication", "actor", "from_status", "to_status", "created_at")
    readonly_fields = ("publication", "actor", "from_status", "to_status", "note", "created_at")
