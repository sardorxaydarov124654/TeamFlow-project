from django.urls import path

from . import views

app_name = "companies"

urlpatterns = [
    path("company/settings/", views.company_settings_view, name="settings"),
    path("companies/create/", views.company_create_view, name="create"),
    path("platform/companies/", views.platform_companies_view, name="platform-list"),
    path(
        "platform/companies/<uuid:pk>/toggle-active/",
        views.platform_company_toggle_active,
        name="platform-toggle-active",
    ),
]
