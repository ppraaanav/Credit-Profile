import uuid
from django.db import models


class Customer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.full_name} <{self.email}>"


class Order(models.Model):
    STATUS_CHOICES = [
        ("placed", "Placed"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
        ("returned", "Returned"),
    ]

    id = models.BigAutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="orders")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="placed")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Order {self.id} - {self.customer}"


class Payment(models.Model):
    METHOD_CHOICES = [
        ("card", "Card"),
        ("cod", "Cash on Delivery"),
        ("wallet", "Wallet"),
        ("bank", "Bank Transfer"),
    ]

    id = models.BigAutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="payments")
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments")
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    success = models.BooleanField(default=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Payment {self.id} - {self.customer} - {self.amount}"


class CreditProfile(models.Model):
    BAND_CHOICES = [
        ("A", "Very Low Risk"),
        ("B", "Low Risk"),
        ("C", "Medium Risk"),
        ("D", "High Risk"),
        ("E", "Very High Risk"),
    ]

    id = models.BigAutoField(primary_key=True)
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, related_name="credit_profile")
    score = models.IntegerField(default=0)
    risk_band = models.CharField(max_length=1, choices=BAND_CHOICES, default="C")
    features = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"CreditProfile({self.customer}) = {self.score} ({self.risk_band})"


class ActivityLog(models.Model):
    SEVERITY_CHOICES = [
        ("info", "Info"),
        ("warning", "Warning"),
        ("error", "Error"),
        ("critical", "Critical"),
    ]
    
    ACTION_CHOICES = [
        ("order_created", "Order Created"),
        ("order_status_changed", "Order Status Changed"),
        ("payment_success", "Payment Success"),
        ("payment_failed", "Payment Failed"),
        ("score_updated", "Score Updated"),
        ("score_recomputed", "Score Recomputed"),
        ("customer_login", "Customer Login"),
        ("profile_viewed", "Profile Viewed"),
        ("report_downloaded", "Report Downloaded"),
        ("customer_created", "Customer Created"),
        ("customer_updated", "Customer Updated"),
    ]

    id = models.BigAutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="activity_logs", null=True, blank=True)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default="info")
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)  # Store additional context like user_id, order_id, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["customer", "-created_at"]),
            models.Index(fields=["action", "-created_at"]),
            models.Index(fields=["severity", "-created_at"]),
        ]

    def __str__(self) -> str:
        customer_str = f"{self.customer}" if self.customer else "System"
        return f"{self.get_action_display()} - {customer_str} - {self.created_at}"


