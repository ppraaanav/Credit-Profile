from django.contrib import admin
from .models import Customer, Order, Payment, CreditProfile, ActivityLog


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "phone", "created_at")
    search_fields = ("full_name", "email", "phone")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "amount", "status", "created_at")
    search_fields = ("id", "customer__full_name", "customer__email")
    list_filter = ("status",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "order", "method", "success", "amount", "created_at")
    list_filter = ("method", "success")
    search_fields = ("id", "customer__full_name", "customer__email")


@admin.register(CreditProfile)
class CreditProfileAdmin(admin.ModelAdmin):
    list_display = ("customer", "score", "risk_band", "updated_at")
    list_filter = ("risk_band",)
    search_fields = ("customer__full_name", "customer__email")


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("action", "customer", "severity", "description", "created_at", "ip_address")
    list_filter = ("action", "severity", "created_at")
    search_fields = ("description", "customer__full_name", "customer__email", "ip_address")
    readonly_fields = ("created_at", "customer", "action", "severity", "description", "metadata", "ip_address", "user_agent")
    date_hierarchy = "created_at"
    
    def has_add_permission(self, request):
        return False  # Prevent manual creation, only via signals/utils


