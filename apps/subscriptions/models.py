from django.db import models
from django.utils import timezone

from apps.companies.models import Company


class SubscriptionPlan(models.Model):
    """Static catalogue of plans — seeded via migration/fixture, edited in admin."""

    code = models.CharField(max_length=20, choices=Company.Plan.choices, unique=True)
    name = models.CharField(max_length=100)
    max_users = models.PositiveIntegerField(null=True, blank=True, help_text="Blank = unlimited")
    max_projects = models.PositiveIntegerField(null=True, blank=True, help_text="Blank = unlimited")
    price_monthly = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    features = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["price_monthly"]

    def __str__(self):
        return self.name


class Subscription(models.Model):
    """
    Mock subscription record per company (no real payment gateway yet, per TZ #16).
    """

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        CANCELED = "canceled", "Canceled"
        PAST_DUE = "past_due", "Past due"

    company = models.OneToOneField(
        Company, on_delete=models.CASCADE, related_name="subscription_record"
    )
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    started_at = models.DateTimeField(default=timezone.now)
    current_period_end = models.DateTimeField(null=True, blank=True)
    is_mock = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.company.name} — {self.plan.name}"

    def sync_company_plan(self):
        """Keep the denormalized Company.plan field in sync for fast limit checks."""
        self.company.plan = self.plan.code
        self.company.save(update_fields=["plan"])
