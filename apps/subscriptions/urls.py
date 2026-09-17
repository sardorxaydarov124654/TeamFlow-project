from django.urls import path

from . import views

app_name = "subscriptions"

urlpatterns = [
    path("subscriptions/plans/", views.plans_list_view, name="plans"),
    path("subscriptions/", views.my_subscription_view, name="mine"),
    path("subscriptions/upgrade/<str:plan_code>/", views.upgrade_view, name="upgrade"),
]
