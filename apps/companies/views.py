from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from apps.common.decorators import platform_admin_required

from .forms import CompanyCreateForm, CompanyForm
from .models import Company


@login_required
def company_settings_view(request):
    company = request.user.company
    if company is None:
        messages.error(request, "You are not attached to a company.")
        return redirect("dashboard:dashboard")

    is_owner = company.owner_id == request.user.id
    can_edit = is_owner or request.user.is_platform_admin

    if request.method == "POST":
        if not can_edit:
            raise PermissionDenied("Only the company owner can update the company.")
        form = CompanyForm(request.POST, request.FILES, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, "Company settings updated.")
            return redirect("companies:settings")
    else:
        form = CompanyForm(instance=company)

    return render(
        request,
        "companies/settings.html",
        {"company": company, "form": form, "can_edit": can_edit},
    )


@login_required
def company_create_view(request):
    if request.method == "POST":
        form = CompanyCreateForm(request.POST, request.FILES)
        if form.is_valid():
            company = form.save(commit=False)
            company.owner = request.user
            company.save()
            messages.success(request, f"{company.name} created.")
            return redirect("companies:settings")
    else:
        form = CompanyCreateForm()
    return render(request, "companies/create.html", {"form": form})


@platform_admin_required
def platform_companies_view(request):
    companies = Company.objects.all()
    return render(request, "companies/platform_list.html", {"companies": companies})


@platform_admin_required
def platform_company_toggle_active(request, pk):
    company = get_object_or_404(Company, pk=pk)
    if request.method == "POST":
        company.is_active = not company.is_active
        company.save(update_fields=["is_active"])
        messages.success(
            request, f"{company.name} is now {'active' if company.is_active else 'blocked'}."
        )
    return redirect("companies:platform-list")
