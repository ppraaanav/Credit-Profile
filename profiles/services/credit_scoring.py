from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Tuple

from django.db.models import Avg, Count, Max, Min, Q, Sum

from ..models import Customer, CreditProfile, Order, Payment


def _safe_decimal(value: Decimal | None) -> Decimal:
    return Decimal("0.00") if value is None else Decimal(value)


def extract_features(customer: Customer) -> Dict[str, float]:
    now = datetime.utcnow()
    window_30d = now - timedelta(days=30)
    window_180d = now - timedelta(days=180)

    orders = Order.objects.filter(customer=customer)
    payments = Payment.objects.filter(customer=customer)

    delivered = orders.filter(status="delivered")
    returned = orders.filter(status="returned")

    # Aggregations
    total_orders = orders.count()
    delivered_orders = delivered.count()
    returned_orders = returned.count()
    return_rate = (returned_orders / delivered_orders) if delivered_orders else 0.0

    total_spend = _safe_decimal(orders.aggregate(s=Sum("amount"))['s'])
    avg_order_value = _safe_decimal(orders.aggregate(a=Avg("amount"))['a'])

    spend_30d = _safe_decimal(orders.filter(created_at__gte=window_30d).aggregate(s=Sum("amount"))['s'])
    spend_180d = _safe_decimal(orders.filter(created_at__gte=window_180d).aggregate(s=Sum("amount"))['s'])

    successful_payments = payments.filter(success=True).count()
    failed_payments = payments.filter(success=False).count()
    failure_rate = (failed_payments / (successful_payments + failed_payments)) if (successful_payments + failed_payments) else 0.0

    uses_cod = payments.filter(method="cod").exists()

    features = {
        "total_orders": float(total_orders),
        "delivered_orders": float(delivered_orders),
        "returned_orders": float(returned_orders),
        "return_rate": float(return_rate),
        "total_spend": float(total_spend),
        "avg_order_value": float(avg_order_value),
        "spend_30d": float(spend_30d),
        "spend_180d": float(spend_180d),
        "failed_payment_rate": float(failure_rate),
        "uses_cod": 1.0 if uses_cod else 0.0,
    }

    return features


def score_from_features(features: Dict[str, float]) -> Tuple[int, str]:
    # Simple rule-based scorecard (0-1000)
    score = 600

    score += min(200, int(features.get("total_spend", 0) / 100.0))
    score += min(100, int(features.get("delivered_orders", 0) * 2))
    score += min(80, int(features.get("avg_order_value", 0) / 10.0))

    score -= int(300 * min(1.0, features.get("return_rate", 0)))
    score -= int(200 * min(1.0, features.get("failed_payment_rate", 0)))
    score -= 50 if features.get("uses_cod", 0) >= 1 else 0

    score = max(300, min(1000, score))

    if score >= 800:
        band = "A"
    elif score >= 700:
        band = "B"
    elif score >= 600:
        band = "C"
    elif score >= 500:
        band = "D"
    else:
        band = "E"

    return score, band


def compute_and_persist_credit_profile(customer: Customer) -> CreditProfile:
    features = extract_features(customer)
    score, band = score_from_features(features)

    profile, _ = CreditProfile.objects.update_or_create(
        customer=customer,
        defaults={
            "score": score,
            "risk_band": band,
            "features": features,
        },
    )
    return profile


