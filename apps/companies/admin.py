from django.contrib import admin

from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "owner",
        "plan",
        "is_active",
        "member_count",
        "project_count",
        "created_at",
    )
    list_filter = ("plan", "is_active", "created_at")
    search_fields = ("name", "slug", "owner__email")
    readonly_fields = ("id", "created_at", "updated_at")
    prepopulated_fields = {"slug": ("name",)}
    actions = ["activate_companies", "deactivate_companies"]

    def member_count(self, obj):
        return obj.members.count()

    def project_count(self, obj):
        return obj.projects.count()

    @admin.action(description="Activate selected companies")
    def activate_companies(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Deactivate selected companies")
    def deactivate_companies(self, request, queryset):
        queryset.update(is_active=False)
