from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.PLATFORM_ADMIN)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom user. Email is the login field. Role + company drive tenant access."""

    class Role(models.TextChoices):
        PLATFORM_ADMIN = "platform_admin", _("Platform Admin")
        MANAGER = "manager", _("Manager")
        EMPLOYEE = "employee", _("Employee")

    username = None
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.EMPLOYEE)
    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="members",
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        # Emails are case-insensitive by convention; normalize so login,
        # invites, and uniqueness checks never diverge on casing.
        if self.email:
            self.email = self.email.lower()
        super().save(*args, **kwargs)

    @property
    def is_platform_admin(self):
        return self.role == self.Role.PLATFORM_ADMIN

    @property
    def is_manager(self):
        return self.role == self.Role.MANAGER

    @property
    def is_employee(self):
        return self.role == self.Role.EMPLOYEE

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email


class CompanyInvitation(models.Model):
    """Pending invite for a new employee/manager to join a company."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        EXPIRED = "expired", "Expired"

    company = models.ForeignKey(
        "companies.Company", on_delete=models.CASCADE, related_name="invitations"
    )
    email = models.EmailField()
    role = models.CharField(
        max_length=20, choices=User.Role.choices, default=User.Role.EMPLOYEE
    )
    invited_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_invitations"
    )
    token = models.CharField(max_length=64, unique=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("company", "email", "status")

    def __str__(self):
        return f"{self.email} -> {self.company.name} ({self.status})"
