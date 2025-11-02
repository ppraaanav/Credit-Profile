from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path
from dotenv import load_dotenv
import os


class Command(BaseCommand):
    help = "Check what's in .env file (masks secrets)"

    def handle(self, *args, **options):
        env_path = settings.BASE_DIR / ".env"
        
        if not env_path.exists():
            self.stdout.write(self.style.ERROR(f".env file not found at: {env_path}"))
            return
        
        self.stdout.write(f".env file found at: {env_path}")
        self.stdout.write("\nReading .env file...")
        
        # Load .env
        load_dotenv(env_path, override=True)
        
        # Check for Google vars
        client_id = os.environ.get("GOOGLE_CLIENT_ID")
        secret = os.environ.get("GOOGLE_CLIENT_SECRET")
        
        self.stdout.write("\nEnvironment variables found:")
        self.stdout.write(f"GOOGLE_CLIENT_ID: {'FOUND' if client_id else 'NOT FOUND'}")
        if client_id:
            self.stdout.write(f"  Value: {client_id[:30]}... (masked)")
        
        self.stdout.write(f"GOOGLE_CLIENT_SECRET: {'FOUND' if secret else 'NOT FOUND'}")
        if secret:
            self.stdout.write(f"  Value: {'*' * min(len(secret), 30)}... (masked)")
        
        # Show raw lines (safe)
        self.stdout.write("\nFirst few lines of .env (to check format):")
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:10]
                for i, line in enumerate(lines, 1):
                    # Mask secret values but show structure
                    if 'SECRET' in line or 'CLIENT_SECRET' in line:
                        parts = line.split('=')
                        if len(parts) == 2:
                            self.stdout.write(f"  Line {i}: {parts[0]}=***MASKED***")
                        else:
                            self.stdout.write(f"  Line {i}: {line.strip()}")
                    elif 'CLIENT_ID' in line:
                        parts = line.split('=')
                        if len(parts) == 2:
                            self.stdout.write(f"  Line {i}: {parts[0]}={parts[1][:20]}...")
                        else:
                            self.stdout.write(f"  Line {i}: {line.strip()}")
                    else:
                        self.stdout.write(f"  Line {i}: {line.strip()}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error reading file: {e}"))

