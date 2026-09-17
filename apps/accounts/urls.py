from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("accounts/register/", views.register_view, name="register"),
    path("accounts/login/", views.EmailLoginView.as_view(), name="login"),
    path("accounts/logout/", views.logout_view, name="logout"),
    path("accounts/profile/", views.profile_view, name="profile"),
    path("invite/accept/<str:token>/", views.accept_invitation_view, name="accept-invitation"),
    path("company/members/", views.members_list_view, name="members"),
    path("company/members/invite/", views.invite_member_view, name="invite-member"),
    path("company/members/<int:pk>/", views.member_detail_view, name="member-detail"),
    path(
        "company/members/<int:pk>/deactivate/",
        views.member_deactivate_view,
        name="member-deactivate",
    ),
]
