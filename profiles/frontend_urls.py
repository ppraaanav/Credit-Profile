from django.urls import path
from .views_frontend import customer_list_page, customer_detail_page, dashboard_page, export_credit_report_pdf, customer_history_page, profile_page, register_page, home_page, customer_dashboard_page, order_create_page, payment_create_page
from .views_audit import audit_logs_page


urlpatterns = [
    path("", home_page, name="home"),
    path("dashboard/", dashboard_page, name="dashboard"),
    path("my-dashboard/", customer_dashboard_page, name="customer-dashboard"),
    path("customers/", customer_list_page, name="customer-list"),
    path("customers/<uuid:customer_id>/", customer_detail_page, name="customer-detail"),
    path("customers/<uuid:customer_id>/history/", customer_history_page, name="customer-history"),
    path("customers/<uuid:customer_id>/credit-report.pdf", export_credit_report_pdf, name="credit-report-pdf"),
    path("orders/new/", order_create_page, name="order-create"),
    path("payments/new/", payment_create_page, name="payment-create"),
    path("profile/", profile_page, name="profile"),
    path("accounts/register/", register_page, name="register"),
    path("audit-logs/", audit_logs_page, name="audit-logs"),
]


