from django.contrib.auth.views import LoginView
from django.shortcuts import redirect


class CustomLoginView(LoginView):
    def get_success_url(self):
        # Log login activity
        try:
            from .utils import log_activity
            from .models import Customer
            
            user = self.request.user
            # Try to find customer by email
            customer = None
            if user.email:
                try:
                    customer = Customer.objects.get(email=user.email)
                except Customer.DoesNotExist:
                    pass
            
            log_activity(
                customer=customer,
                action="customer_login",
                severity="info",
                description=f"User {user.username} logged in",
                metadata={
                    "username": user.username,
                    "is_staff": user.is_staff,
                    "user_id": user.id,
                },
                request=self.request,
            )
        except Exception:
            pass  # Don't break login if logging fails
        
        # Redirect based on user type
        if self.request.user.is_staff:
            return "/dashboard/"
        else:
            return "/my-dashboard/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        google_enabled = False
        try:
            from django.conf import settings
            from pathlib import Path
            from dotenv import load_dotenv
            import os
            
            # Load .env to check for Google OAuth credentials
            env_path = settings.BASE_DIR / ".env"
            load_dotenv(env_path, override=True)
            
            client_id = os.environ.get("GOOGLE_CLIENT_ID")
            secret = os.environ.get("GOOGLE_CLIENT_SECRET")
            
            if client_id and secret:
                from allauth.socialaccount.models import SocialApp
                from django.contrib.sites.models import Site
                # Try to get or create SocialApp
                site = Site.objects.get_current(self.request)
                app, created = SocialApp.objects.get_or_create(
                    provider="google",
                    defaults={
                        "name": "Google",
                        "client_id": client_id,
                        "secret": secret,
                    }
                )
                
                # Update if credentials changed
                if not created:
                    if app.client_id != client_id or app.secret != secret:
                        app.client_id = client_id
                        app.secret = secret
                        app.save()
                
                # Link to site if not linked
                if site not in app.sites.all():
                    app.sites.add(site)
                
                google_enabled = app.client_id and app.secret and (site in app.sites.all())
        except Exception:
            pass
        
        context["google_enabled"] = google_enabled
        return context

