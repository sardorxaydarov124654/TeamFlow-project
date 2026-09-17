"""
Plain Django view decorators that replace the old DRF permission classes.
Each one wraps a view function and redirects/denies before the view body runs.
"""
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def company_member_required(view_func):
    """User must belong to a company (i.e. not a platform admin with no tenant)."""

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.company_id is None and not request.user.is_platform_admin:
            messages.error(request, "You are not attached to a company yet.")
            return redirect("dashboard:home")
        return view_func(request, *args, **kwargs)

    return wrapper


def manager_required(view_func):
    """Managers and platform admins may write; everyone else is denied."""

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        user = request.user
        if not (user.is_manager or user.is_platform_admin):
            raise PermissionDenied("Only a manager can perform this action.")
        return view_func(request, *args, **kwargs)

    return wrapper


def platform_admin_required(view_func):
    """Full-platform staff only (superuser dashboards, cross-company ops)."""

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_platform_admin:
            raise PermissionDenied("Platform admin access required.")
        return view_func(request, *args, **kwargs)

    return wrapper


def same_company_object(user, obj):
    """
    Object-level tenant isolation check.
    Never trust the URL/PK alone — always re-check company ownership on the object.
    """
    if user.is_platform_admin:
        return True
    obj_company_id = getattr(obj, "company_id", None)
    if obj_company_id is None and hasattr(obj, "company"):
        obj_company_id = obj.company.id
    return obj_company_id is not None and obj_company_id == user.company_id


def company_scoped_queryset(user, queryset, company_field="company"):
    """Scope a queryset to the user's own company (platform admins see everything)."""
    if user.is_platform_admin:
        return queryset
    if user.company_id is None:
        return queryset.none()
    return queryset.filter(**{company_field: user.company_id})
