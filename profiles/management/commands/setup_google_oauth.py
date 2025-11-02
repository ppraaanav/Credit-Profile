from django.core.management.base import BaseCommand
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
import os
from dotenv import load_dotenv


class Command(BaseCommand):
    help = "Setup Google OAuth from environment variables"

    def handle(self, *args, **options):
        from pathlib import Path
        from django.conf import settings
        BASE_DIR = settings.BASE_DIR
        env_path = BASE_DIR / ".env"
        
        # Load .env file
        load_dotenv(env_path)
        
        # Check if .env file exists
        if not env_path.exists():
            self.stdout.write(self.style.ERROR(f".env file not found at: {env_path}"))
            self.stdout.write("Please create a .env file in the project root with:")
            self.stdout.write("GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com")
            self.stdout.write("GOOGLE_CLIENT_SECRET=your-client-secret")
            return
        
        client_id = os.environ.get("GOOGLE_CLIENT_ID")
        secret = os.environ.get("GOOGLE_CLIENT_SECRET")
        
        self.stdout.write(f"Looking for env vars in: {env_path}")
        
        if not client_id or not secret:
            self.stdout.write(self.style.ERROR("GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET not found in environment"))
            self.stdout.write(self.style.WARNING("Please add them to your .env file:"))
            self.stdout.write("GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com")
            self.stdout.write("GOOGLE_CLIENT_SECRET=your-client-secret")
            return
        
        try:
            site = Site.objects.get_current()
            self.stdout.write(f"Using site: {site.domain} (ID: {site.id})")
            
            app, created = SocialApp.objects.get_or_create(
                provider="google",
                defaults={
                    "name": "Google",
                    "client_id": client_id,
                    "secret": secret,
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS("Created Google SocialApp"))
            else:
                app.client_id = client_id
                app.secret = secret
                app.save()
                self.stdout.write(self.style.SUCCESS("Updated existing Google SocialApp"))
            
            if site not in app.sites.all():
                app.sites.add(site)
                self.stdout.write(self.style.SUCCESS(f"Added site {site.domain} to Google SocialApp"))
            else:
                self.stdout.write(self.style.SUCCESS("Site already linked to Google SocialApp"))
            
            self.stdout.write(self.style.SUCCESS(f"\nGoogle OAuth configured successfully!"))
            self.stdout.write(f"Client ID: {app.client_id[:30]}...")
            self.stdout.write(f"Linked to site: {app.sites.all()[0].domain if app.sites.exists() else 'None'}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))

