from .models import ActivityLog


def client_ip(request):
    if request is None:
        return None
    fwd = request.META.get("HTTP_X_FORWARDED_FOR")
    return (fwd.split(",")[0].strip() if fwd else request.META.get("REMOTE_ADDR")) or None


def log(user, category, message, request=None):
    ActivityLog.objects.create(user=user if getattr(user, "pk", None) else None, category=category,
                               message=str(message)[:500], ip=client_ip(request))
