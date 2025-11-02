from django.core.management.base import BaseCommand

from ....profiles.models import Customer
from ....profiles.services.credit_scoring import compute_and_persist_credit_profile


class Command(BaseCommand):
    help = "Recompute credit scores for all customers"

    def handle(self, *args, **options):
        total = 0
        for customer in Customer.objects.all().iterator():
            compute_and_persist_credit_profile(customer)
            total += 1
        self.stdout.write(self.style.SUCCESS(f"Recomputed credit scores for {total} customers"))


