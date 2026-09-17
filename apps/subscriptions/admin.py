from django.contrib import admin

from .models import Subscription, SubscriptionPlan


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "max_users", "max_projects", "price_monthly")


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("company", "plan", "status", "started_at", "current_period_end")
    list_filter = ("status", "plan")
    search_fields = ("company__name",)
    autocomplete_fields = ("company",)
