"""Email authentication backend."""
from django.contrib.auth.backends import ModelBackend

from accounts.models import User


class EmailBackend(ModelBackend):
    """Authenticate using email address."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        email = kwargs.get('email', username)
        if email is None or password is None:
            return None
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
