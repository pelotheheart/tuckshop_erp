from django.contrib.auth import views as auth_views
from django.urls import path
from . import views
from . TERPLoginView import TERPLoginView

urlpatterns = [
    path("login/", TERPLoginView.as_view(template_name="accounts/login.html", redirect_authenticated_user=True), name="login",),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("accounts/register", views.register, name="register"),
    path("accounts/staff", views.staff, name="staff"),
    path("accounts/staff/add", views.add_staff, name="add_staff"),
    path("accounts/staff/edit/<int:user_id>/", views.edit_details, name="edit_staff"),
    path("accounts/staff/user_details/<int:user_id>/", views.user_details, name="user_details"),
    path("accounts/staff/my_profile/<int:user_id>/", views.my_profile, name="my_profile"),
    path("accounts/staff/edit_my_profile/", views.edit_my_profile, name="edit_my_profile"),
    path("accounts/staff/deactivate/<int:user_id>/", views.deactivate_user, name="deactivate_user"),
    path("accounts/staff/activate/<int:user_id>/", views.activate_user, name="activate_user"),
    path("accounts/staff/reset_password/<int:user_id>/", views.reset_password, name="reset_password"),
    path("accounts/branches/", views.branches, name="branches"),
    path("accounts/branches/add_branch", views.add_branch, name="add_branch"),
    path("accounts/branches/branch_details/<int:branch_id>", views.edit_branch, name="branch_details")


]
