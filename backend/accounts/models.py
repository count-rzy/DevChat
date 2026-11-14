
import secrets

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


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


class UserProfile(models.Model):
    LANGUAGE_CHOICES = [("en", "English"), ("ru", "Russian")]

    user = models.OneToOneField(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="profile",
    )
    display_name = models.CharField(max_length=80, blank=True)
    description = models.CharField(max_length=500, blank=True)
    preferred_language = models.CharField(
        max_length=2,
        choices=LANGUAGE_CHOICES,
        default="en",
    )

    def __str__(self):
        return self.display_name or self.user.get_username()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
