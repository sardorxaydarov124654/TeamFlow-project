from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from apps.common.decorators import (
    company_member_required,
    company_scoped_queryset,
    manager_required,
    same_company_object,
)

from .forms import CommentForm, TaskForm
from .models import Task


def _notify_assignment(task):
    from apps.notifications.services import notify_user

    if task.assigned_to_id:
        notify_user(
            user=task.assigned_to,
            title="New task assigned",
            message=f'You were assigned to "{task.title}"',
            notif_type="task_assigned",
            extra={"task_id": task.id, "project_id": task.project_id},
        )


def _notify_status_change(task):
    from apps.notifications.services import notify_user

    recipients = {task.created_by, task.assigned_to} - {None}
    for recipient in recipients:
        notify_user(
            user=recipient,
            title="Task status updated",
            message=f'"{task.title}" is now {task.get_status_display()}',
            notif_type="task_status_changed",
            extra={"task_id": task.id, "status": task.status},
        )


def _notify_new_comment(comment):
    from apps.notifications.services import notify_user

    task = comment.task
    recipients = {task.created_by, task.assigned_to} - {None, comment.author}
    for recipient in recipients:
        notify_user(
            user=recipient,
            title="New comment",
            message=f'{comment.author.full_name} commented on "{task.title}"',
            notif_type="comment_added",
            extra={"task_id": task.id, "comment_id": comment.id},
        )


@company_member_required
def task_list_view(request):
    qs = company_scoped_queryset(
        request.user,
        Task.objects.select_related("project", "company", "assigned_to", "created_by"),
    )

    status = request.GET.get("status")
    priority = request.GET.get("priority")
    project_id = request.GET.get("project")
    assigned_to = request.GET.get("assigned_to")
    search = request.GET.get("q")
    ordering = request.GET.get("ordering", "-created_at")

    if status:
        qs = qs.filter(status=status)
    if priority:
        qs = qs.filter(priority=priority)
    if project_id:
        qs = qs.filter(project_id=project_id)
    if assigned_to:
        qs = qs.filter(assigned_to_id=assigned_to)
    if search:
        from django.db.models import Q

        qs = qs.filter(Q(title__icontains=search) | Q(description__icontains=search))
    if ordering in {"deadline", "-deadline", "created_at", "-created_at", "priority", "-priority"}:
        qs = qs.order_by(ordering)

    return render(
        request,
        "tasks/list.html",
        {
            "tasks": qs,
            "status_choices": Task.Status.choices,
            "priority_choices": Task.Priority.choices,
            "current_status": status or "",
            "current_priority": priority or "",
            "search": search or "",
            "ordering": ordering,
        },
    )


@company_member_required
def task_create_view(request):
    user = request.user
    if user.is_employee:
        raise PermissionDenied("Employees cannot create tasks.")
    company = user.company
    if company is None:
        messages.error(request, "You are not attached to a company.")
        return redirect("dashboard:dashboard")

    if request.method == "POST":
        form = TaskForm(request.POST, company=company)
        if form.is_valid():
            task = form.save(commit=False)
            task.company = company
            task.created_by = user
            task.save()
            _notify_assignment(task)
            messages.success(request, f'Task "{task.title}" created.')
            return redirect("tasks:detail", pk=task.pk)
    else:
        form = TaskForm(company=company)
    return render(request, "tasks/form.html", {"form": form, "mode": "create"})


@company_member_required
def task_detail_view(request, pk):
    qs = company_scoped_queryset(
        request.user, Task.objects.select_related("project", "company", "assigned_to", "created_by")
    )
    task = get_object_or_404(qs, pk=pk)
    if not same_company_object(request.user, task):
        raise PermissionDenied

    comments = task.comments.select_related("author")

    if request.method == "POST":
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.task = task
            comment.company = task.company
            comment.author = request.user
            comment.save()
            _notify_new_comment(comment)
            messages.success(request, "Comment added.")
            return redirect("tasks:detail", pk=task.pk)
    else:
        comment_form = CommentForm()

    return render(
        request,
        "tasks/detail.html",
        {"task": task, "comments": comments, "comment_form": comment_form},
    )


@manager_required
def task_edit_view(request, pk):
    qs = company_scoped_queryset(request.user, Task.objects.all())
    task = get_object_or_404(qs, pk=pk)
    if not same_company_object(request.user, task):
        raise PermissionDenied

    old_status = task.status
    old_assignee_id = task.assigned_to_id

    if request.method == "POST":
        form = TaskForm(request.POST, instance=task, company=task.company)
        if form.is_valid():
            task = form.save()
            if task.assigned_to_id and task.assigned_to_id != old_assignee_id:
                _notify_assignment(task)
            if task.status != old_status:
                _notify_status_change(task)
            messages.success(request, "Task updated.")
            return redirect("tasks:detail", pk=task.pk)
    else:
        form = TaskForm(instance=task, company=task.company)
    return render(request, "tasks/form.html", {"form": form, "mode": "edit", "task": task})


@manager_required
def task_delete_view(request, pk):
    qs = company_scoped_queryset(request.user, Task.objects.all())
    task = get_object_or_404(qs, pk=pk)
    if not same_company_object(request.user, task):
        raise PermissionDenied
    if request.method == "POST":
        title = task.title
        task.delete()
        messages.success(request, f'Task "{title}" deleted.')
        return redirect("tasks:list")
    return render(request, "tasks/confirm_delete.html", {"task": task})
