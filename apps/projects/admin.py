from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "company", "owner", "status", "deadline", "created_at")
    list_filter = ("status", "company")
    search_fields = ("name", "company__name")
    autocomplete_fields = ("owner", "company")
    readonly_fields = ("created_at", "updated_at")
