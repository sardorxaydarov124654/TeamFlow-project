import uuid

from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Company(models.Model):
    """A tenant. Every business record in the system hangs off a Company."""

    class Plan(models.TextChoices):
        FREE = "free", "Free"
        PRO = "pro", "Pro"
        BUSINESS = "business", "Business"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    logo = models.ImageField(upload_to="company_logos/", blank=True, null=True)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_companies",
    )
    plan = models.CharField(max_length=20, choices=Plan.choices, default=Plan.FREE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "companies"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)[:240]
            slug = base_slug
            i = 1
            while Company.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f"{base_slug}-{i}"
            self.slug = slug
        super().save(*args, **kwargs)

    # --- Subscription limit helpers -------------------------------------
    @property
    def subscription(self):
        return getattr(self, "subscription_record", None)

    def get_user_limit(self):
        limits = {self.Plan.FREE: 3, self.Plan.PRO: 50, self.Plan.BUSINESS: None}
        return limits.get(self.plan)

    def get_project_limit(self):
        limits = {self.Plan.FREE: 5, self.Plan.PRO: None, self.Plan.BUSINESS: None}
        return limits.get(self.plan)

    def can_add_user(self):
        limit = self.get_user_limit()
        if limit is None:
            return True
        return self.members.filter(is_active=True).count() < limit

    def can_add_project(self):
        limit = self.get_project_limit()
        if limit is None:
            return True
        return self.projects.count() < limit
