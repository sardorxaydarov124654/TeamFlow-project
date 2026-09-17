from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    path("notifications/", views.notifications_list_view, name="list"),
    path("notifications/<int:pk>/mark-read/", views.notification_mark_read_view, name="mark-read"),
    path("notifications/mark-all-read/", views.notifications_mark_all_read_view, name="mark-all-read"),
]
