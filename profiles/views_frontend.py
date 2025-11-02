from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.db import models
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .models import CreditProfile, Customer, Order, Payment
from .forms import OrderForm, PaymentForm
from .services.credit_scoring import compute_and_persist_credit_profile


def home_page(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect("dashboard")
        else:
            return redirect("customer-dashboard")
    return redirect("login")


@login_required
@user_passes_test(lambda u: u.is_staff)
def customer_list_page(request: HttpRequest) -> HttpResponse:
    customers = Customer.objects.order_by("-created_at")[:200]
    return render(request, "profiles/customer_list.html", {"customers": customers})


@login_required
def customer_detail_page(request: HttpRequest, customer_id) -> HttpResponse:
    from .utils import log_activity
    
    customer = get_object_or_404(Customer, id=customer_id)
    profile = getattr(customer, "credit_profile", None)
    orders = customer.orders.order_by("-created_at")[:50]
    payments = customer.payments.order_by("-created_at")[:50]

    if request.method == "POST" and request.user.is_staff and request.POST.get("action") == "recompute":
        compute_and_persist_credit_profile(customer)
        log_activity(
            customer=customer,
            action="score_recomputed",
            severity="info",
            description=f"Credit score manually recomputed by {request.user.username}",
            metadata={"user_id": request.user.id, "username": request.user.username},
            request=request,
        )
        return redirect(reverse("customer-detail", kwargs={"customer_id": customer.id}))
    
    # Log profile view
    log_activity(
        customer=customer,
        action="profile_viewed",
        severity="info",
        description=f"Profile viewed by {request.user.username}",
        metadata={"viewer_id": request.user.id, "viewer_username": request.user.username},
        request=request,
    )

    return render(
        request,
        "profiles/customer_detail.html",
        {"customer": customer, "profile": profile, "orders": orders, "payments": payments},
    )


@login_required
@user_passes_test(lambda u: u.is_staff)
def order_create_page(request: HttpRequest) -> HttpResponse:
    from .utils import log_activity
    initial = {}
    customer_id = request.GET.get("customer")
    if customer_id:
        try:
            initial["customer"] = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            pass
    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save()
            # Recompute score
            compute_and_persist_credit_profile(order.customer)
            # Log activity
            log_activity(
                customer=order.customer,
                action="order_created",
                severity="info",
                description=f"Order #{order.id} created via form by {request.user.username}",
                metadata={"user_id": request.user.id, "order_id": order.id},
                request=request,
            )
            return redirect("customer-detail", customer_id=order.customer.id)
    else:
        form = OrderForm(initial=initial)
    return render(request, "profiles/order_form.html", {"form": form})


@login_required
@user_passes_test(lambda u: u.is_staff)
def payment_create_page(request: HttpRequest) -> HttpResponse:
    from .utils import log_activity
    initial = {}
    customer_id = request.GET.get("customer")
    order_id = request.GET.get("order")
    if customer_id:
        try:
            initial["customer"] = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            pass
    if order_id:
        try:
            initial["order"] = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            pass
    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save()
            # Recompute score
            compute_and_persist_credit_profile(payment.customer)
            # Log activity
            log_activity(
                customer=payment.customer,
                action="payment_success" if payment.success else "payment_failed",
                severity="info" if payment.success else "warning",
                description=f"Payment #{payment.id} created via form by {request.user.username}",
                metadata={"user_id": request.user.id, "payment_id": payment.id},
                request=request,
            )
            return redirect("customer-detail", customer_id=payment.customer.id)
    else:
        form = PaymentForm(initial=initial)
    return render(request, "profiles/payment_form.html", {"form": form})


@login_required
def customer_dashboard_page(request: HttpRequest) -> HttpResponse:
    """Customer-facing dashboard showing their own credit profile and transactions"""
    user = request.user
    customer = None
    
    # Find customer by email
    if user.email:
        try:
            customer = Customer.objects.get(email=user.email)
        except Customer.DoesNotExist:
            pass
    
    if not customer:
        # Create customer if doesn't exist
        if user.email:
            customer = Customer.objects.create(
                full_name=user.get_full_name() or user.username,
                email=user.email,
                phone=""
            )
        else:
            return render(request, "profiles/customer_dashboard.html", {
                "customer": None,
                "profile": None,
                "error": "Please update your email in your profile to view your credit information."
            })
    
    profile = getattr(customer, "credit_profile", None)
    orders = customer.orders.order_by("-created_at")[:10]
    payments = customer.payments.order_by("-created_at")[:10]
    
    # Calculate stats
    total_orders = customer.orders.count()
    delivered_orders = customer.orders.filter(status="delivered").count()
    returned_orders = customer.orders.filter(status="returned").count()
    total_spend = customer.orders.filter(status="delivered").aggregate(s=models.Sum("amount"))['s'] or 0
    successful_payments = customer.payments.filter(success=True).count()
    total_payments = customer.payments.count()
    
    # Calculate percentages
    return_rate_pct = round((returned_orders / delivered_orders * 100) if delivered_orders else 0, 1)
    payment_success_rate_pct = round((successful_payments / total_payments * 100) if total_payments else 0, 1)
    
    return render(request, "profiles/customer_dashboard.html", {
        "customer": customer,
        "profile": profile,
        "orders": orders,
        "payments": payments,
        "total_orders": total_orders,
        "delivered_orders": delivered_orders,
        "returned_orders": returned_orders,
        "return_rate_pct": return_rate_pct,
        "total_spend": total_spend,
        "successful_payments": successful_payments,
        "total_payments": total_payments,
        "payment_success_rate_pct": payment_success_rate_pct,
    })


@login_required
@user_passes_test(lambda u: u.is_staff)
def dashboard_page(request: HttpRequest) -> HttpResponse:
    """Admin/Staff dashboard - full system overview"""
    from django.db.models import Sum, Count, Avg, Q
    from datetime import datetime, timedelta
    
    profiles = CreditProfile.objects.select_related("customer")
    customers = Customer.objects.all()
    orders = Order.objects.all()
    payments = Payment.objects.all()
    
    # Basic counts
    total_profiles = profiles.count()
    total_customers = customers.count()
    total_orders = orders.count()
    total_payments = payments.count()
    
    # Score metrics
    avg_score = int(profiles.aggregate(_avg=Avg("score"))['_avg'] or 0)
    min_score = profiles.aggregate(_min=models.Min("score"))['_min'] or 0
    max_score = profiles.aggregate(_max=models.Max("score"))['_max'] or 0
    
    # Risk bands
    bands = {b: profiles.filter(risk_band=b).count() for b in ["A", "B", "C", "D", "E"]}
    high_risk = profiles.filter(risk_band__in=["D", "E"]).count()
    low_risk = profiles.filter(risk_band__in=["A", "B"]).count()
    risk_percentage = round((high_risk / total_profiles * 100) if total_profiles else 0, 1)
    
    # Order metrics
    delivered = orders.filter(status="delivered").count()
    returned = orders.filter(status="returned").count()
    cancelled = orders.filter(status="cancelled").count()
    return_rate_pct = round((returned / delivered * 100) if delivered else 0, 2)
    cancelled_rate_pct = round((cancelled / total_orders * 100) if total_orders else 0, 2)
    total_revenue = orders.filter(status="delivered").aggregate(s=Sum("amount"))['s'] or 0
    
    # Payment metrics
    successful_payments = payments.filter(success=True).count()
    failed_payments = payments.filter(success=False).count()
    payment_success_rate = round((successful_payments / total_payments * 100) if total_payments else 0, 2)
    cod_count = payments.filter(method="cod").count()
    cod_pct = round((cod_count / total_payments * 100) if total_payments else 0, 2)
    
    # Recent activity (last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_orders = orders.filter(created_at__gte=thirty_days_ago).count()
    recent_customers = customers.filter(created_at__gte=thirty_days_ago).count()
    
    # Payment methods distribution
    payment_methods = {
        "Card": payments.filter(method="card").count(),
        "COD": payments.filter(method="cod").count(),
        "Wallet": payments.filter(method="wallet").count(),
        "Bank": payments.filter(method="bank").count(),
    }
    
    # Order status distribution
    order_statuses = {
        "Delivered": delivered,
        "Shipped": orders.filter(status="shipped").count(),
        "Placed": orders.filter(status="placed").count(),
        "Returned": returned,
        "Cancelled": cancelled,
    }
    
    # Calculate percentages for progress bars
    low_risk_pct = round((low_risk / total_profiles * 100) if total_profiles else 0, 1)
    medium_risk_pct = round((bands.get("C", 0) / total_profiles * 100) if total_profiles else 0, 1)
    high_risk_pct = round((high_risk / total_profiles * 100) if total_profiles else 0, 1)

    return render(
        request,
        "profiles/dashboard.html",
        {
            "total_profiles": total_profiles,
            "total_customers": total_customers,
            "total_orders": total_orders,
            "total_payments": total_payments,
            "avg_score": avg_score,
            "min_score": min_score,
            "max_score": max_score,
            "high_risk": high_risk,
            "low_risk": low_risk,
            "risk_percentage": risk_percentage,
            "low_risk_pct": low_risk_pct,
            "medium_risk_pct": medium_risk_pct,
            "high_risk_pct": high_risk_pct,
            "cod_pct": cod_pct,
            "return_rate_pct": return_rate_pct,
            "cancelled_rate_pct": cancelled_rate_pct,
            "payment_success_rate": payment_success_rate,
            "failed_payments": failed_payments,
            "total_revenue": total_revenue,
            "recent_orders": recent_orders,
            "recent_customers": recent_customers,
            "bands": bands,
            "payment_methods": payment_methods,
            "order_statuses": order_statuses,
        },
    )


@login_required
def export_credit_report_pdf(request: HttpRequest, customer_id) -> HttpResponse:
    from .utils import log_activity
    
    # Lazy import to avoid hard dependency if not used
    from io import BytesIO
    from xhtml2pdf import pisa
    customer = get_object_or_404(Customer, id=customer_id)
    profile = getattr(customer, "credit_profile", None)
    
    # Log report download
    log_activity(
        customer=customer,
        action="report_downloaded",
        severity="info",
        description=f"Credit report PDF downloaded by {request.user.username}",
        metadata={"user_id": request.user.id, "username": request.user.username},
        request=request,
    )

    html = render(
        request,
        "profiles/credit_report.html",
        {"customer": customer, "profile": profile},
    ).content.decode("utf-8")

    pdf_io = BytesIO()
    pisa.CreatePDF(html, dest=pdf_io)
    response = HttpResponse(pdf_io.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f"attachment; filename=credit_report_{customer.id}.pdf"
    return response


@login_required
def customer_history_page(request: HttpRequest, customer_id) -> HttpResponse:
    customer = get_object_or_404(Customer, id=customer_id)
    orders = list(customer.orders.all().values("id", "status", "amount", "created_at"))
    payments = list(customer.payments.all().values("id", "method", "success", "amount", "created_at"))

    events = []
    for o in orders:
        severity = "success" if o["status"] == "delivered" else ("failed" if o["status"] == "returned" else "risk" if o["status"] == "cancelled" else "neutral")
        events.append({
            "ts": o["created_at"],
            "kind": "order",
            "title": f"Order #{o['id']} {o['status']}",
            "amount": o["amount"],
            "severity": severity,
        })
    for p in payments:
        severity = "success" if p["success"] else "failed"
        events.append({
            "ts": p["created_at"],
            "kind": "payment",
            "title": f"Payment #{p['id']} {('OK' if p['success'] else 'Failed')} ({p['method']})",
            "amount": p["amount"],
            "severity": severity,
        })

    events.sort(key=lambda e: e["ts"], reverse=True)

    suspicious = []
    recent_orders = sorted(orders, key=lambda x: x["created_at"], reverse=True)[:5]
    recent_returns = sum(1 for o in recent_orders if o["status"] == "returned")
    total_delivered = sum(1 for o in orders if o["status"] == "delivered")
    total_returns = sum(1 for o in orders if o["status"] == "returned")
    return_rate = (total_returns / total_delivered) if total_delivered else 0.0
    if recent_returns >= 2 or return_rate >= 0.30:
        suspicious.append({
            "icon": "⚠️",
            "title": "Sudden spike in returns",
            "detail": f"Recent returns: {recent_returns} in last 5; overall: {return_rate:.0%}",
            "severity": "risk",
        })

    recent_payments = sorted(payments, key=lambda x: x["created_at"], reverse=True)
    streak = 0
    max_streak = 0
    for p in recent_payments:
        if not p["success"]:
            streak += 1
            if streak > max_streak:
                max_streak = streak
        else:
            streak = 0
    if max_streak >= 2:
        suspicious.append({
            "icon": "❌",
            "title": "Failed payments streak",
            "detail": f"Longest consecutive failures: {max_streak}",
            "severity": "failed",
        })

    return render(
        request,
        "profiles/customer_history.html",
        {"customer": customer, "events": events, "suspicious": suspicious},
    )


@login_required
def profile_page(request: HttpRequest) -> HttpResponse:
    user = request.user
    return render(request, "profiles/profile.html", {"user_obj": user})


def _create_customer_for_user(user: User) -> None:
    # Create Customer record if not exists, keyed by email when possible
    if not user.email:
        return
    if not Customer.objects.filter(email=user.email).exists():
        Customer.objects.create(full_name=user.get_full_name() or user.username, email=user.email, phone="")


def register_page(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("dashboard")
    error = None
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        confirm = request.POST.get("confirm", "")
        full_name = request.POST.get("full_name", "").strip()
        if not username or not email or not password:
            error = "Please fill in all required fields."
        elif password != confirm:
            error = "Passwords do not match."
        elif User.objects.filter(username=username).exists():
            error = "Username already taken."
        elif User.objects.filter(email=email).exists():
            error = "Email already in use."
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            if full_name:
                first, *rest = full_name.split(" ")
                user.first_name = first
                user.last_name = " ".join(rest)
                user.save()
            _create_customer_for_user(user)
            auth_user = authenticate(request, username=username, password=password)
            if auth_user:
                login(request, auth_user)
                if auth_user.is_staff:
                    return redirect("dashboard")
                else:
                    return redirect("customer-dashboard")
    
    # Check if Google OAuth is enabled (auto-setup if .env has credentials)
    google_enabled = False
    try:
        from django.conf import settings
        from pathlib import Path
        from dotenv import load_dotenv
        import os
        from allauth.socialaccount.models import SocialApp
        from django.contrib.sites.models import Site
        
        # Load .env to check for Google OAuth credentials
        env_path = settings.BASE_DIR / ".env"
        load_dotenv(env_path, override=True)
        
        client_id = os.environ.get("GOOGLE_CLIENT_ID")
        secret = os.environ.get("GOOGLE_CLIENT_SECRET")
        
        if client_id and secret:
            # Try to get or create SocialApp
            site = Site.objects.get_current(request)
            app, created = SocialApp.objects.get_or_create(
                provider="google",
                defaults={
                    "name": "Google",
                    "client_id": client_id,
                    "secret": secret,
                }
            )
            
            # Update if credentials changed
            if not created:
                if app.client_id != client_id or app.secret != secret:
                    app.client_id = client_id
                    app.secret = secret
                    app.save()
            
            # Link to site if not linked
            if site not in app.sites.all():
                app.sites.add(site)
            
            google_enabled = app.client_id and app.secret and (site in app.sites.all())
    except Exception:
        pass
    
    return render(request, "registration/register.html", {"error": error, "google_enabled": google_enabled})

