from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Type(models.TextChoices):
        TASK_ASSIGNED = "task_assigned", "Task assigned"
        TASK_STATUS_CHANGED = "task_status_changed", "Task status changed"
        COMMENT_ADDED = "comment_added", "Comment added"
        DEADLINE_REMINDER = "deadline_reminder", "Deadline reminder"
        COMPANY_INVITATION = "company_invitation", "Company invitation"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    title = models.CharField(max_length=255)
    message = models.TextField(blank=True)
    type = models.CharField(max_length=30, choices=Type.choices)
    data = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "is_read"])]

    def __str__(self):
        return f"{self.title} -> {self.user}"
