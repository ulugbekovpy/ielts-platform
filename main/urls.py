from django.urls import path
from .views import register_view, email_confirmation_view, dashboard, plans_view, login_view, logout_view, homepage, oferta

urlpatterns = [
    path("", homepage, name="home"),
    path("register/", register_view, name="register"),
    path("confirm-email/", email_confirmation_view, name="email_confirmation"),
    path("plans/", plans_view, name="plans"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("dashboard/", dashboard, name="dashboard"),
    path("oferta/", oferta, name="oferta")
]