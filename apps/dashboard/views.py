from django.core.cache import cache
from django.db.models import Count, Q
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.common.decorators import company_member_required
from apps.projects.models import Project
from apps.tasks.models import Task

CACHE_TTL_SECONDS = 60  # short TTL: stats stay fresh, DB still gets protected from bursts


def home_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:dashboard")
    return render(request, "dashboard/home.html")


@company_member_required
def dashboard_view(request):
    company = request.user.company
    if company is None:
        # Platform admins with no tenant land on the cross-company view instead.
        return redirect("companies:platform-list")

    cache_key = f"dashboard:company:{company.id}"
    data = cache.get(cache_key)
    if data is None:
        data = _compute_stats(company)
        cache.set(cache_key, data, CACHE_TTL_SECONDS)
    return render(request, "dashboard/dashboard.html", {"stats": data, "company": company})


def _compute_stats(company):
    projects = Project.objects.filter(company=company)
    tasks = Task.objects.filter(company=company)
    now = timezone.now()

    return {
        "total_employees": company.members.filter(is_active=True).count(),
        "active_projects": projects.filter(status=Project.Status.ACTIVE).count(),
        "completed_projects": projects.filter(status=Project.Status.COMPLETED).count(),
        "pending_tasks": tasks.exclude(status=Task.Status.DONE).count(),
        "overdue_tasks": tasks.filter(deadline__lt=now).exclude(status=Task.Status.DONE).count(),
        "completed_tasks": tasks.filter(status=Task.Status.DONE).count(),
        "employee_productivity": _employee_productivity(company),
        "generated_at": now,
    }


def _employee_productivity(company):
    rows = (
        company.members.filter(is_active=True)
        .annotate(
            assigned=Count("assigned_tasks", distinct=True),
            completed=Count(
                "assigned_tasks",
                filter=Q(assigned_tasks__status=Task.Status.DONE),
                distinct=True,
            ),
        )
        .values("id", "first_name", "last_name", "email", "assigned", "completed")
    )
    return list(rows)
