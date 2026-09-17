from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.projects.models import Project
from apps.tasks.models import Task


def _invalidate(company_id):
    if company_id:
        cache.delete(f"dashboard:company:{company_id}")


@receiver(post_save, sender=Task)
@receiver(post_delete, sender=Task)
def invalidate_dashboard_on_task_change(sender, instance, **kwargs):
    _invalidate(instance.company_id)


@receiver(post_save, sender=Project)
@receiver(post_delete, sender=Project)
def invalidate_dashboard_on_project_change(sender, instance, **kwargs):
    _invalidate(instance.company_id)
