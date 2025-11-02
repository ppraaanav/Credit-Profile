from allauth.account.signals import user_logged_in
from allauth.socialaccount.signals import social_account_added, pre_social_login
from django.dispatch import receiver
from django.contrib.sessions.models import Session
from .utils import log_activity
from .models import Customer


@receiver(pre_social_login)
def pre_social_login_handler(sender, request, sociallogin, **kwargs):
    """Set redirect URL before social login completes"""
    # Store redirect URL in session
    if sociallogin.is_existing:
        # Existing user - check if staff
        if sociallogin.user.is_staff:
            request.session['login_redirect'] = '/dashboard/'
        else:
            request.session['login_redirect'] = '/my-dashboard/'
    else:
        # New user - default to customer dashboard (they won't be staff)
        request.session['login_redirect'] = '/my-dashboard/'


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log user login (works for both regular and social login)"""
    try:
        # Try to find customer by email
        customer = None
        if user.email:
            try:
                customer = Customer.objects.get(email=user.email)
            except Customer.DoesNotExist:
                pass
        
        login_method = "social" if kwargs.get("sociallogin") else "regular"
        description = f"User {user.username} logged in via {login_method}"
        
        log_activity(
            customer=customer,
            action="customer_login",
            severity="info",
            description=description,
            metadata={
                "username": user.username,
                "is_staff": user.is_staff,
                "user_id": user.id,
                "login_method": login_method,
            },
            request=request,
        )
        
        # Auto-create customer if doesn't exist and user has email
        if not customer and user.email and login_method == "social":
            try:
                customer = Customer.objects.create(
                    full_name=user.get_full_name() or user.username,
                    email=user.email,
                    phone=""
                )
            except Exception:
                pass
    except Exception:
        pass  # Don't break login flow

