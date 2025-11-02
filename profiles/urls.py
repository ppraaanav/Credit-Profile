from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CreditProfileViewSet, CustomerViewSet, OrderViewSet, PaymentViewSet
from .permissions import IsAdminOrReadOnly


router = DefaultRouter()
router.register(r"customers", CustomerViewSet, basename="customer")
router.register(r"orders", OrderViewSet, basename="order")
router.register(r"payments", PaymentViewSet, basename="payment")
router.register(r"credit-profiles", CreditProfileViewSet, basename="credit-profile")


urlpatterns = [
    path("", include(router.urls)),
]


