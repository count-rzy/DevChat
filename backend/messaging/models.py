from django.conf import settings
from django.db import models
from django.db.models import F, Q


class Conversation(models.Model):
    member_one = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations_as_first_member",
    )
    member_two = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations_as_second_member",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["member_one", "member_two"],
                name="unique_private_conversation_pair",
            ),
            models.CheckConstraint(
                condition=Q(member_one__lt=F("member_two")),
                name="conversation_members_ordered",
            ),
        ]

    def includes(self, user):
        return user.pk in (self.member_one_id, self.member_two_id)


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages",
    )
    content = models.TextField(max_length=4000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "pk"]
        indexes = [
            models.Index(fields=["conversation", "created_at", "id"]),
        ]
