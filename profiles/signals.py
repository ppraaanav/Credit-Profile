from django.db.models.signals import post_save, post_init
from django.dispatch import receiver
from django.db import transaction

from .models import Order, Payment, CreditProfile
from .services.credit_scoring import compute_and_persist_credit_profile
from .utils import log_activity


@receiver(post_save, sender=Order)
def recompute_on_order(sender, instance: Order, created: bool, **kwargs):
    # Log activity
    action = "order_created" if created else "order_status_changed"
    severity = "error" if instance.status == "returned" else ("warning" if instance.status == "cancelled" else "info")
    description = f"Order #{instance.id} {instance.status} - Amount: ₹{instance.amount}"
    
    log_activity(
        customer=instance.customer,
        action=action,
        severity=severity,
        description=description,
        metadata={
            "order_id": instance.id,
            "order_status": instance.status,
            "order_amount": str(instance.amount),
        }
    )
    
    # Recompute on create or significant updates
    compute_and_persist_credit_profile(instance.customer)


@receiver(post_save, sender=Payment)
def recompute_on_payment(sender, instance: Payment, created: bool, **kwargs):
    # Log activity
    action = "payment_success" if instance.success else "payment_failed"
    severity = "error" if not instance.success else "info"
    description = f"Payment #{instance.id} {'successful' if instance.success else 'failed'} - Method: {instance.method} - Amount: ₹{instance.amount}"
    
    metadata = {
        "payment_id": instance.id,
        "payment_method": instance.method,
        "payment_amount": str(instance.amount),
        "payment_success": instance.success,
    }
    if instance.order:
        metadata["order_id"] = instance.order.id
    
    log_activity(
        customer=instance.customer,
        action=action,
        severity=severity,
        description=description,
        metadata=metadata,
    )
    
    compute_and_persist_credit_profile(instance.customer)


@receiver(post_save, sender=CreditProfile)
def log_score_update(sender, instance: CreditProfile, created: bool, **kwargs):
    action = "score_recomputed" if created else "score_updated"
    description = f"Credit score updated: {instance.score} (Risk Band: {instance.risk_band})"
    
    log_activity(
        customer=instance.customer,
        action=action,
        severity="info",
        description=description,
        metadata={
            "score": instance.score,
            "risk_band": instance.risk_band,
            "previous_score": kwargs.get("previous_score"),
        }
    )



