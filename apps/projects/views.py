from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from apps.common.decorators import (
    company_member_required,
    company_scoped_queryset,
    manager_required,
    same_company_object,
)

from .forms import ProjectForm
from .models import Project


@company_member_required
def project_list_view(request):
    qs = company_scoped_queryset(
        request.user, Project.objects.select_related("owner", "company")
    )

    status = request.GET.get("status")
    search = request.GET.get("q")
    ordering = request.GET.get("ordering", "-created_at")

    if status:
        qs = qs.filter(status=status)
    if search:
        from django.db.models import Q

        qs = qs.filter(Q(name__icontains=search) | Q(description__icontains=search))
    if ordering in {"created_at", "-created_at", "deadline", "-deadline", "name", "-name"}:
        qs = qs.order_by(ordering)

    return render(
        request,
        "projects/list.html",
        {
            "projects": qs,
            "status_choices": Project.Status.choices,
            "current_status": status or "",
            "search": search or "",
            "ordering": ordering,
        },
    )


@manager_required
def project_create_view(request):
    company = request.user.company
    if company is None:
        messages.error(request, "You are not attached to a company.")
        return redirect("dashboard:dashboard")
    if not company.can_add_project():
        messages.error(request, "Your subscription plan's project limit has been reached.")
        return redirect("projects:list")

    if request.method == "POST":
        form = ProjectForm(request.POST, company=company)
        if form.is_valid():
            project = form.save(commit=False)
            project.company = company
            if not project.owner_id:
                project.owner = request.user
            project.save()
            messages.success(request, f'Project "{project.name}" created.')
            return redirect("projects:detail", pk=project.pk)
    else:
        form = ProjectForm(company=company, initial={"owner": request.user})
    return render(request, "projects/form.html", {"form": form, "mode": "create"})


@company_member_required
def project_detail_view(request, pk):
    qs = company_scoped_queryset(request.user, Project.objects.select_related("owner", "company"))
    project = get_object_or_404(qs, pk=pk)
    if not same_company_object(request.user, project):
        raise PermissionDenied
    return render(
        request,
        "projects/detail.html",
        {"project": project, "task_stats": project.task_stats},
    )


@manager_required
def project_edit_view(request, pk):
    qs = company_scoped_queryset(request.user, Project.objects.all())
    project = get_object_or_404(qs, pk=pk)
    if not same_company_object(request.user, project):
        raise PermissionDenied

    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project, company=project.company)
        if form.is_valid():
            form.save()
            messages.success(request, "Project updated.")
            return redirect("projects:detail", pk=project.pk)
    else:
        form = ProjectForm(instance=project, company=project.company)
    return render(request, "projects/form.html", {"form": form, "mode": "edit", "project": project})


@manager_required
def project_delete_view(request, pk):
    qs = company_scoped_queryset(request.user, Project.objects.all())
    project = get_object_or_404(qs, pk=pk)
    if not same_company_object(request.user, project):
        raise PermissionDenied
    if request.method == "POST":
        name = project.name
        project.delete()
        messages.success(request, f'Project "{name}" deleted.')
        return redirect("projects:list")
    return render(request, "projects/confirm_delete.html", {"project": project})
