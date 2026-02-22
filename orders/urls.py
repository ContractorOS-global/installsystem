from django.urls import path
from django.contrib.auth import views as auth_views
from .views import wallet_view

urlpatterns = [
    # кошелёк
    path("", wallet_view, name="wallet"),
    path("wallet/", wallet_view, name="wallet"),

    # логин/логаут
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="/login/"), name="logout"),
]
