from django.urls import path

from . import views

app_name = "tasks"

urlpatterns = [
    path("tasks/", views.task_list_view, name="list"),
    path("tasks/create/", views.task_create_view, name="create"),
    path("tasks/<int:pk>/", views.task_detail_view, name="detail"),
    path("tasks/<int:pk>/edit/", views.task_edit_view, name="edit"),
    path("tasks/<int:pk>/delete/", views.task_delete_view, name="delete"),
]
