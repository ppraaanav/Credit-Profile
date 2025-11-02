from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import CreditProfile, Customer, Order, Payment
from .serializers import (
    CreditProfileSerializer,
    CustomerSerializer,
    OrderSerializer,
    PaymentSerializer,
)
from .services.credit_scoring import compute_and_persist_credit_profile


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by("-created_at")
    serializer_class = CustomerSerializer
    search_fields = ["full_name", "email", "phone"]
    ordering_fields = ["created_at", "full_name", "email"]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy", "recompute_score"]:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    @action(detail=True, methods=["post"], url_path="recompute-score")
    def recompute_score(self, request, pk=None):
        customer = self.get_object()
        profile = compute_and_persist_credit_profile(customer)
        return Response(CreditProfileSerializer(profile).data)

    @action(detail=True, methods=["get"], url_path="credit-profile")
    def credit_profile(self, request, pk=None):
        customer = self.get_object()
        profile = getattr(customer, "credit_profile", None)
        if not profile:
            return Response({"detail": "No profile yet"}, status=status.HTTP_404_NOT_FOUND)
        return Response(CreditProfileSerializer(profile).data)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by("-created_at")
    serializer_class = OrderSerializer
    filterset_fields = ["status", "customer"]
    ordering_fields = ["created_at", "amount"]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all().order_by("-created_at")
    serializer_class = PaymentSerializer
    filterset_fields = ["method", "success", "customer", "order"]
    ordering_fields = ["created_at", "amount"]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]


class CreditProfileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CreditProfile.objects.select_related("customer").all().order_by("-updated_at")
    serializer_class = CreditProfileSerializer
    filterset_fields = ["risk_band"]
    search_fields = ["customer__full_name", "customer__email"]
    ordering_fields = ["updated_at", "score"]

    def get_permissions(self):
        return [permissions.IsAuthenticated()]


