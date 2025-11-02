from django.contrib import admin
from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from profiles.views_auth import CustomLoginView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", CustomLoginView.as_view(), name="login"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/", include("allauth.urls")),
    path("api/", include("profiles.urls")),
    path("api/token/", obtain_auth_token, name="api-token"),
    path("", include("profiles.frontend_urls")),
]


