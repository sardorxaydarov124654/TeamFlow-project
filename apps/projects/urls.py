from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
    path("projects/", views.project_list_view, name="list"),
    path("projects/create/", views.project_create_view, name="create"),
    path("projects/<int:pk>/", views.project_detail_view, name="detail"),
    path("projects/<int:pk>/edit/", views.project_edit_view, name="edit"),
    path("projects/<int:pk>/delete/", views.project_delete_view, name="delete"),
]
