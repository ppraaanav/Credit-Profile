from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from .models import ActivityLog, Customer


@login_required
@user_passes_test(lambda u: u.is_staff)
def audit_logs_page(request: HttpRequest) -> HttpResponse:
    logs = ActivityLog.objects.select_related("customer").all()
    
    # Filters
    customer_id = request.GET.get("customer")
    action_filter = request.GET.get("action")
    severity_filter = request.GET.get("severity")
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")
    search = request.GET.get("search")
    
    if customer_id:
        try:
            customer = Customer.objects.get(id=customer_id)
            logs = logs.filter(customer=customer)
        except Customer.DoesNotExist:
            pass
    
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    if severity_filter:
        logs = logs.filter(severity=severity_filter)
    
    if date_from:
        try:
            logs = logs.filter(created_at__gte=date_from)
        except Exception:
            pass
    
    if date_to:
        try:
            # Add one day to include the entire day
            date_to_obj = timezone.datetime.strptime(date_to, "%Y-%m-%d")
            date_to_obj = date_to_obj + timedelta(days=1)
            logs = logs.filter(created_at__lt=date_to_obj)
        except Exception:
            pass
    
    if search:
        logs = logs.filter(
            Q(description__icontains=search) |
            Q(customer__full_name__icontains=search) |
            Q(customer__email__icontains=search)
        )
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(logs, 50)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_logs = logs.count()
    error_count = logs.filter(severity__in=["error", "critical"]).count()
    today_count = logs.filter(created_at__gte=timezone.now().replace(hour=0, minute=0, second=0)).count()
    
    context = {
        "logs": page_obj,
        "total_logs": total_logs,
        "error_count": error_count,
        "today_count": today_count,
        "action_choices": ActivityLog.ACTION_CHOICES,
        "severity_choices": ActivityLog.SEVERITY_CHOICES,
        "customers": Customer.objects.all().order_by("-created_at")[:100],
        "filters": {
            "customer": customer_id,
            "action": action_filter,
            "severity": severity_filter,
            "date_from": date_from,
            "date_to": date_to,
            "search": search,
        }
    }
    
    return render(request, "profiles/audit_logs.html", context)

