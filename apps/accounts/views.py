from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.views import LoginView
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

from apps.common.decorators import company_member_required, manager_required
from apps.companies.models import Company

from .forms import (
    EmailAuthenticationForm,
    InviteMemberForm,
    MemberRoleForm,
    ProfileForm,
    RegisterForm,
)
from .models import CompanyInvitation, User
from .tasks import send_invitation_email


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:dashboard")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = User(
                    email=form.cleaned_data["email"],
                    first_name=form.cleaned_data.get("first_name", ""),
                    last_name=form.cleaned_data.get("last_name", ""),
                    role=User.Role.MANAGER,
                )
                user.set_password(form.cleaned_data["password"])
                user.save()
                company = Company.objects.create(
                    name=form.cleaned_data["company_name"], owner=user
                )
                user.company = company
                user.save(update_fields=["company"])
            auth_login(request, user)
            messages.success(request, f"Welcome to TeamFlow, {user.first_name or user.email}!")
            return redirect("dashboard:dashboard")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


class EmailLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True


def logout_view(request):
    auth_logout(request)
    messages.success(request, "You have been signed out.")
    return redirect("accounts:login")


def profile_view(request):
    if not request.user.is_authenticated:
        return redirect("accounts:login")
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user)
    return render(request, "accounts/profile.html", {"form": form})


@company_member_required
def members_list_view(request):
    user = request.user
    if user.is_platform_admin:
        members = User.objects.all()
    else:
        members = User.objects.filter(company_id=user.company_id)
    return render(request, "accounts/members_list.html", {"members": members})


@company_member_required
def member_detail_view(request, pk):
    user = request.user
    qs = User.objects.all() if user.is_platform_admin else User.objects.filter(company_id=user.company_id)
    member = get_object_or_404(qs, pk=pk)

    can_edit = user.is_manager or user.is_platform_admin
    if request.method == "POST" and can_edit:
        form = MemberRoleForm(request.POST, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, f"{member.full_name} updated.")
            return redirect("accounts:members")
    else:
        form = MemberRoleForm(instance=member) if can_edit else None

    return render(
        request,
        "accounts/member_detail.html",
        {"member": member, "form": form, "can_edit": can_edit},
    )


@company_member_required
def member_deactivate_view(request, pk):
    user = request.user
    if not (user.is_manager or user.is_platform_admin):
        messages.error(request, "Only a manager can deactivate a teammate.")
        return redirect("accounts:members")
    qs = User.objects.all() if user.is_platform_admin else User.objects.filter(company_id=user.company_id)
    member = get_object_or_404(qs, pk=pk)
    if request.method == "POST":
        # Soft-delete: deactivate rather than hard-delete a teammate's account.
        member.is_active = False
        member.save(update_fields=["is_active"])
        messages.success(request, f"{member.full_name} has been deactivated.")
    return redirect("accounts:members")


@manager_required
def invite_member_view(request):
    if not request.user.company_id:
        messages.error(request, "You are not attached to a company.")
        return redirect("dashboard:dashboard")

    company = request.user.company
    if not company.can_add_user():
        messages.error(request, "Your subscription plan's user limit has been reached.")
        return redirect("accounts:members")

    if request.method == "POST":
        form = InviteMemberForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            role = form.cleaned_data["role"]
            import secrets

            invitation, _ = CompanyInvitation.objects.update_or_create(
                company=company,
                email=email,
                status=CompanyInvitation.Status.PENDING,
                defaults={
                    "role": role,
                    "invited_by": request.user,
                    "token": secrets.token_urlsafe(32),
                },
            )
            send_invitation_email.delay(
                invitation.email, company.name, invitation.token, invitation.role
            )
            messages.success(request, f"Invitation sent to {email}.")
            return redirect("accounts:members")
    else:
        form = InviteMemberForm()
    return render(request, "accounts/invite_member.html", {"form": form})


def accept_invitation_view(request, token):
    invitation = get_object_or_404(
        CompanyInvitation, token=token, status=CompanyInvitation.Status.PENDING
    )
    if request.method == "POST":
        password = request.POST.get("password", "")
        first_name = request.POST.get("first_name", "")
        last_name = request.POST.get("last_name", "")
        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters.")
        else:
            with transaction.atomic():
                user = User(
                    email=invitation.email,
                    first_name=first_name,
                    last_name=last_name,
                    role=invitation.role,
                    company=invitation.company,
                )
                user.set_password(password)
                user.save()
                invitation.status = CompanyInvitation.Status.ACCEPTED
                invitation.save(update_fields=["status"])
            auth_login(request, user)
            messages.success(request, f"Welcome to {invitation.company.name}!")
            return redirect("dashboard:dashboard")
    return render(request, "accounts/accept_invitation.html", {"invitation": invitation})
