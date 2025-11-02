from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.http import HttpRequest, HttpResponse
from allauth.socialaccount.models import SocialAccount


def google_callback_redirect(request: HttpRequest) -> HttpResponse:
    """Handle redirect after Google OAuth callback"""
    if request.user.is_authenticated:
        # Check if user is staff
        if request.user.is_staff:
            return redirect("/dashboard/")
        else:
            return redirect("/my-dashboard/")
    return redirect("/accounts/login/")

