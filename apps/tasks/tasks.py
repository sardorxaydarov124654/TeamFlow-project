import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def send_deadline_reminders():
    """
    Celery Beat job (runs every N minutes — see config/settings/base.py
    CELERY_BEAT_SCHEDULE). Notifies the assignee of any task whose deadline
    is within the next 24h and hasn't been reminded about yet.
    """
    from apps.notifications.services import notify_user

    from .models import Task

    soon = timezone.now() + timedelta(hours=24)
    qs = Task.objects.filter(
        deadline__isnull=False,
        deadline__lte=soon,
        deadline__gte=timezone.now(),
        deadline_reminder_sent=False,
        assigned_to__isnull=False,
    ).exclude(status=Task.Status.DONE)

    count = 0
    for task in qs.select_related("assigned_to"):
        notify_user(
            user=task.assigned_to,
            title="Deadline approaching",
            message=f'"{task.title}" is due soon.',
            notif_type="deadline_reminder",
            extra={"task_id": task.id, "deadline": task.deadline.isoformat()},
        )
        task.deadline_reminder_sent = True
        task.save(update_fields=["deadline_reminder_sent"])
        count += 1

    logger.info("send_deadline_reminders: notified %s task(s)", count)
    return count
