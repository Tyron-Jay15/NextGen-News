"""Dashboard services."""
from dashboard.models import AuditLog


class AuditService:
    @staticmethod
    def log_action(user, action: str, ip_address: str = '', object_type: str = '', object_id: str = '', details: dict = None):
        AuditLog.objects.create(
            user=user,
            action=action,
            ip_address=ip_address or None,
            object_type=object_type,
            object_id=object_id,
            details=details or {},
        )
