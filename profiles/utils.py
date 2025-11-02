from .models import ActivityLog
from django.utils import timezone


def log_activity(
    customer=None,
    action="",
    severity="info",
    description="",
    metadata=None,
    request=None,
):
    """Utility function to log activities"""
    ip_address = None
    user_agent = ""
    
    if request:
        ip_address = get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")[:500]  # Limit length
    
    ActivityLog.objects.create(
        customer=customer,
        action=action,
        severity=severity,
        description=description,
        metadata=metadata or {},
        ip_address=ip_address,
        user_agent=user_agent,
    )


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip

