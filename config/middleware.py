"""Custom middleware for security, analytics, and audit logging."""
import logging
from typing import Callable

from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware:
    """Add security headers for production readiness."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        response['X-Content-Type-Options'] = 'nosniff'
        return response


class AnalyticsMiddleware(MiddlewareMixin):
    """Track visitor analytics for public pages."""

    SKIP_PREFIXES = ('/static/', '/media/', '/admin/', '/api/', '/dashboard/')

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        if response.status_code != 200:
            return response
        if any(request.path.startswith(p) for p in self.SKIP_PREFIXES):
            return response
        try:
            from analytics.services import AnalyticsService
            AnalyticsService.log_visit(request)
        except Exception:
            logger.exception('Failed to log analytics visit')
        return response


class AuditLogMiddleware(MiddlewareMixin):
    """Log authenticated admin/dashboard actions."""

    AUDIT_PREFIXES = ('/dashboard/', '/admin/')

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        if request.method not in ('POST', 'PUT', 'PATCH', 'DELETE'):
            return response
        if not any(request.path.startswith(p) for p in self.AUDIT_PREFIXES):
            return response
        if not request.user.is_authenticated:
            return response
        try:
            from dashboard.services import AuditService
            AuditService.log_action(
                user=request.user,
                action=f'{request.method} {request.path}',
                ip_address=self._get_client_ip(request),
            )
        except Exception:
            logger.exception('Failed to write audit log')
        return response

    @staticmethod
    def _get_client_ip(request: HttpRequest) -> str:
        forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if forwarded:
            return forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')
