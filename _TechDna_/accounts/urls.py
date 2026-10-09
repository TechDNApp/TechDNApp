from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView

from .views import register_view, profile, profile_edit

app_name = "accounts"

urlpatterns = [
    path("login/", LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("register/", register_view, name="register"),
    path("profile/", profile, name="profile"),
    path("profile/edit/", profile_edit, name="profile_edit"),
]
