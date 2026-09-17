from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm

from .models import User


class EmailAuthenticationForm(AuthenticationForm):
    """AuthenticationForm already keys off USERNAME_FIELD ('email' here)."""

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_active:
            raise forms.ValidationError("This account is disabled.", code="inactive")


class RegisterForm(forms.Form):
    """
    Self-service registration. The registering user becomes the OWNER of a
    brand new Company (role=manager) вЂ” this is how tenants get created.
    """

    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Confirm password")
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    company_name = forms.CharField(max_length=255, label="Company name")

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def clean_password(self):
        password = self.cleaned_data["password"]
        password_validation.validate_password(password)
        return password

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password") and cleaned.get("password_confirm"):
            if cleaned["password"] != cleaned["password_confirm"]:
                self.add_error("password_confirm", "Passwords do not match.")
        return cleaned


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "avatar"]


class InviteMemberForm(forms.Form):
    email = forms.EmailField()
    role = forms.ChoiceField(
        choices=[
            (User.Role.MANAGER, "Manager"),
            (User.Role.EMPLOYEE, "Employee"),
        ],
        initial=User.Role.EMPLOYEE,
    )


class MemberRoleForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["role", "is_active"]
