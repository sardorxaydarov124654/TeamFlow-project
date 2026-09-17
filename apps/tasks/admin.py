from django.contrib import admin

from .models import Comment, Task


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ("author", "body", "created_at")
    can_delete = False


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "project",
        "company",
        "assigned_to",
        "priority",
        "status",
        "deadline",
    )
    list_filter = ("status", "priority", "company")
    search_fields = ("title", "description")
    autocomplete_fields = ("project", "company", "assigned_to", "created_by")
    readonly_fields = ("created_at", "updated_at")
    inlines = [CommentInline]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("task", "author", "company", "created_at")
    search_fields = ("body",)
    list_filter = ("company",)
