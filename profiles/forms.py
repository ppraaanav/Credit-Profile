from django import forms

from .models import Order, Payment


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["customer", "amount", "status"]


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["customer", "order", "method", "success", "amount"]


