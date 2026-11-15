
from django.urls import path

from .views import (
    current_user,
    csrf_token,
    dev_registration_page,
    log_in,
    log_out,
    manage_my_avatar,
    my_profile,
    public_profile,
    public_profiles,
    register,
    update_my_profile,
    user_avatar,
)


urlpatterns = [
    path("dev/register/", dev_registration_page, name="dev-registration"),
    path("csrf/", csrf_token, name="csrf-token"),
    path("register/", register, name="register"),
    path("login/", log_in, name="login"),
    path("logout/", log_out, name="logout"),
    path("me/", current_user, name="current-user"),
    path("profile/", my_profile, name="my-profile"),
    path("profile/update/", update_my_profile, name="update-my-profile"),
    path("profile/avatar/", manage_my_avatar, name="manage-my-avatar"),
    path("users/", public_profiles, name="public-profiles"),
    path("users/<int:user_id>/", public_profile, name="public-profile"),
    path("users/<int:user_id>/avatar/", user_avatar, name="user-avatar"),
]
