from rest_framework import serializers

from .models import CreditProfile, Customer, Order, Payment


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "full_name", "email", "phone", "created_at"]
        read_only_fields = ["id", "created_at"]


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["id", "customer", "amount", "status", "created_at"]
        read_only_fields = ["id", "created_at"]


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "customer", "order", "method", "success", "amount", "created_at"]
        read_only_fields = ["id", "created_at"]


class CreditProfileSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)

    class Meta:
        model = CreditProfile
        fields = ["id", "customer", "score", "risk_band", "features", "updated_at"]
        read_only_fields = ["id", "updated_at", "score", "risk_band", "features"]


