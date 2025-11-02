import random
from datetime import datetime, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from profiles.models import Customer, Order, Payment
from profiles.services.credit_scoring import compute_and_persist_credit_profile


FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Reyansh", "Muhammad",
    "Sai", "Advik", "Atharv", "Ishaan", "Kabir", "Anaya", "Aadhya", "Sara",
    "Diya", "Myra", "Ira", "Aarohi", "Aaradhya",
]

LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Patel", "Khan", "Iyer", "Reddy", "Das",
    "Nair", "Mehta", "Kapoor", "Joshi", "Chopra", "Bose", "Malhotra",
]

EMAIL_DOMAINS = ["example.com", "mail.com", "test.io", "demo.co"]

ORDER_STATUSES = ["placed", "shipped", "delivered", "cancelled", "returned"]
PAYMENT_METHODS = ["card", "cod", "wallet", "bank"]


def _random_name() -> str:
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def _random_email(name: str, idx: int) -> str:
    base = name.lower().replace(" ", ".")
    return f"{base}.{idx}@{random.choice(EMAIL_DOMAINS)}"


def _random_amount() -> Decimal:
    return Decimal(random.randint(199, 14999)) / Decimal(1)


class Command(BaseCommand):
    help = "Generate 10–15 sample customers with orders, payments, and computed credit profiles"

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=12, help="How many customers to create (default: 12)")

    @transaction.atomic
    def handle(self, *args, **options):
        count = max(10, min(int(options["count"]), 50))
        self.stdout.write(self.style.MIGRATE_HEADING(f"Seeding {count} customers with sample data..."))

        created_customers = []

        # Create customers
        for i in range(count):
            name = _random_name()
            email = _random_email(name, i + random.randint(0, 999))
            customer, _ = Customer.objects.get_or_create(
                email=email,
                defaults={
                    "full_name": name,
                    "phone": f"+91{random.randint(6000000000, 9999999999)}",
                },
            )
            created_customers.append(customer)

        # For each customer, generate orders and payments
        now = datetime.now()
        total_orders = 0
        total_payments = 0

        for customer in created_customers:
            # Vary volumes per customer
            num_orders = random.randint(2, 8)
            num_payments = random.randint(max(1, num_orders - 2), num_orders + 2)

            # Orders
            orders = []
            for j in range(num_orders):
                status_weights = [3, 3, 8, 1, 1]  # bias towards delivered
                status = random.choices(ORDER_STATUSES, weights=status_weights, k=1)[0]
                created_at = now - timedelta(days=random.randint(1, 200))
                order = Order.objects.create(
                    customer=customer,
                    amount=_random_amount(),
                    status=status,
                    created_at=created_at,
                )
                orders.append(order)
                total_orders += 1

            # Payments
            for k in range(num_payments):
                method = random.choice(PAYMENT_METHODS)
                # Fail a few payments esp. with COD
                success = random.choices([True, False], weights=[9, 1 if method != "cod" else 3], k=1)[0]
                related_order = random.choice(orders) if orders and random.random() < 0.8 else None
                created_at = now - timedelta(days=random.randint(1, 200))
                Payment.objects.create(
                    customer=customer,
                    order=related_order,
                    method=method,
                    success=success,
                    amount=_random_amount(),
                    created_at=created_at,
                )
                total_payments += 1

            # Compute credit profile
            compute_and_persist_credit_profile(customer)

        self.stdout.write(self.style.SUCCESS(
            f"Done. Created/updated {len(created_customers)} customers, {total_orders} orders, {total_payments} payments."
        ))


