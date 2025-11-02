import random
from datetime import datetime, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from profiles.models import Customer, Order, Payment
from profiles.services.credit_scoring import compute_and_persist_credit_profile


ORDER_STATUSES = ["placed", "shipped", "delivered", "cancelled", "returned"]
PAYMENT_METHODS = ["card", "cod", "wallet", "bank"]


def _random_amount() -> Decimal:
    return Decimal(random.randint(199, 19999)) / Decimal(1)


class Command(BaseCommand):
    help = "Seed orders and payments for a specific customer email with diverse types"

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True, help="Customer email to seed activity for")
        parser.add_argument("--orders", type=int, default=10, help="Number of orders to create (default: 10)")
        parser.add_argument("--payments", type=int, default=10, help="Number of payments to create (default: 10)")

    @transaction.atomic
    def handle(self, *args, **options):
        email: str = options["email"].strip()
        num_orders: int = max(0, int(options["orders"]))
        num_payments: int = max(0, int(options["payments"]))

        try:
            customer = Customer.objects.get(email=email)
        except Customer.DoesNotExist as exc:
            raise CommandError(f"Customer with email '{email}' does not exist. Create it first.") from exc

        now = datetime.now()
        self.stdout.write(self.style.MIGRATE_HEADING(
            f"Seeding activity for {customer.full_name} <{customer.email}>: {num_orders} orders, {num_payments} payments"
        ))

        orders = []
        # Create orders with a spread of statuses (ensure diversity)
        status_cycle = (ORDER_STATUSES * ((num_orders // len(ORDER_STATUSES)) + 1))[:num_orders]
        for idx in range(num_orders):
            status = status_cycle[idx]
            created_at = now - timedelta(days=random.randint(1, 120))
            order = Order.objects.create(
                customer=customer,
                amount=_random_amount(),
                status=status,
                created_at=created_at,
            )
            orders.append(order)

        # Create payments with diverse methods and some failures (esp. COD)
        method_cycle = (PAYMENT_METHODS * ((num_payments // len(PAYMENT_METHODS)) + 1))[:num_payments]
        for idx in range(num_payments):
            method = method_cycle[idx]
            # Failures: small chance overall; slightly higher for COD
            success = random.choices(
                [True, False],
                weights=[9, 1 if method != "cod" else 3],
                k=1,
            )[0]
            related_order = random.choice(orders) if orders and random.random() < 0.85 else None
            created_at = now - timedelta(days=random.randint(1, 120))
            Payment.objects.create(
                customer=customer,
                order=related_order,
                method=method,
                success=success,
                amount=_random_amount(),
                created_at=created_at,
            )

        # Recompute credit profile
        compute_and_persist_credit_profile(customer)

        self.stdout.write(self.style.SUCCESS(
            f"Done. Added {len(orders)} orders and {num_payments} payments, and recomputed credit score."
        ))


