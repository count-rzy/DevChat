
from django.urls import path

from .views import (
    current_user,
    csrf_token,
    dev_registration_page,
    log_in,
    log_out,
    register,
)


urlpatterns = [
    path("dev/register/", dev_registration_page, name="dev-registration"),
    path("csrf/", csrf_token, name="csrf-token"),
    path("register/", register, name="register"),
    path("login/", log_in, name="login"),
    path("logout/", log_out, name="logout"),
    path("me/", current_user, name="current-user"),
]
