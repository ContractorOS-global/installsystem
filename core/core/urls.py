from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # Django login/logout/password views:
    # /accounts/login/  /accounts/logout/  /accounts/password_change/ ...
    path("accounts/", include("django.contrib.auth.urls")),

    # Your app urls
    path("", include("orders.urls")),
]
