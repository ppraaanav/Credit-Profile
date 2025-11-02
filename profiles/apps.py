from django.apps import AppConfig


class ProfilesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "profiles"
    verbose_name = "Credit Profiles"

    def ready(self):
        from . import signals  # noqa: F401
        from . import social_signals  # noqa: F401
        # Auto-configure Google SocialApp if env vars are present
        import os
        try:
            from allauth.socialaccount.models import SocialApp
            from django.contrib.sites.models import Site
        except Exception:
            return
        client_id = os.environ.get("GOOGLE_CLIENT_ID")
        secret = os.environ.get("GOOGLE_CLIENT_SECRET")
        if client_id and secret:
            try:
                site = Site.objects.get_current()
                app, _ = SocialApp.objects.get_or_create(
                    provider="google",
                    defaults={"name": "Google", "client_id": client_id, "secret": secret},
                )
                # Update if changed
                changed = False
                if app.client_id != client_id:
                    app.client_id = client_id
                    changed = True
                if app.secret != secret:
                    app.secret = secret
                    changed = True
                if changed:
                    app.save()
                if site not in app.sites.all():
                    app.sites.add(site)
            except Exception:
                # Avoid blocking startup if Sites not migrated yet
                pass


