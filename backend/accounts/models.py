
import secrets

from django.db import models


def generate_invite_code():
    return secrets.token_urlsafe(12)


class InviteCode(models.Model):
    code = models.CharField(
        max_length=32,
        unique=True,
        default=generate_invite_code,
    )
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        status = "used" if self.is_used else "available"
        return f"{self.code} ({status})"
