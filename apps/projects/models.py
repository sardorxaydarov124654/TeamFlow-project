from django.conf import settings
from django.db import models


class Project(models.Model):
    class Status(models.TextChoices):
        PLANNING = "planning", "Planning"
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        ARCHIVED = "archived", "Archived"

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="owned_projects",
    )
    company = models.ForeignKey(
        "companies.Company", on_delete=models.CASCADE, related_name="projects"
    )
    start_date = models.DateField(null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PLANNING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["company", "status"])]

    def __str__(self):
        return f"{self.name} ({self.company.name})"

    @property
    def task_stats(self):
        qs = self.tasks.all()
        return {
            "total": qs.count(),
            "todo": qs.filter(status="todo").count(),
            "in_progress": qs.filter(status="in_progress").count(),
            "review": qs.filter(status="review").count(),
            "done": qs.filter(status="done").count(),
        }
