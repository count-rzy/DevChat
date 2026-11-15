import time

from channels.auth import get_user
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.db.models import Q

from .events import conversation_group_name
from .models import Conversation, Message
from .serializers import message_payload

SESSION_RECHECK_SECONDS = 30


@database_sync_to_async
def user_is_conversation_member(user_id, conversation_id):
    return Conversation.objects.filter(pk=conversation_id).filter(
        Q(member_one_id=user_id) | Q(member_two_id=user_id)
    ).exists()


@database_sync_to_async
def serialized_message_for_user(message_id, user_id):
    try:
        message = Message.objects.select_related(
            "sender__profile",
            "reply_to__sender__profile",
        ).prefetch_related("reactions__user").get(pk=message_id)
    except Message.DoesNotExist:
        return None
    return message_payload(message, viewer_id=user_id)


class ConversationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if not user.is_authenticated:
            await self.close(code=4401)
            return

        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        if not await user_is_conversation_member(user.pk, self.conversation_id):
            await self.close(code=4404)
            return

        self.group_name = conversation_group_name(self.conversation_id)
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        self.session_checked_at = time.monotonic()
        await self.accept()

    async def disconnect(self, close_code):
        group_name = getattr(self, "group_name", None)
        if group_name:
            await self.channel_layer.group_discard(group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        if content == {"type": "typing", "is_typing": True}:
            now = time.monotonic()
            if now - getattr(self, "last_typing_event_at", 0) >= 1:
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        "type": "typing.changed",
                        "user_id": self.scope["user"].pk,
                        "is_typing": True,
                    },
                )
                self.last_typing_event_at = now
            return
        if content == {"type": "typing", "is_typing": False}:
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "typing.changed",
                    "user_id": self.scope["user"].pk,
                    "is_typing": False,
                },
            )
            return
        if content != {"type": "ping"}:
            return

        now = time.monotonic()
        if now - self.session_checked_at >= SESSION_RECHECK_SECONDS:
            # Reload the session from its backend so logout and expiry invalidate
            # an already-open socket as well as future HTTP requests.
            session_key = self.scope["session"].session_key
            refreshed_session = self.scope["session"].__class__(session_key=session_key)
            self.scope["session"] = refreshed_session
            user = await get_user(self.scope)
            if not user.is_authenticated or user.pk != self.scope["user"].pk:
                await self.close(code=4401)
                return
            self.scope["user"] = user
            self.session_checked_at = now

        await self.send_json({"type": "pong"})

    async def message_event(self, event):
        message = await serialized_message_for_user(
            event["message_id"],
            self.scope["user"].pk,
        )
        if message is not None:
            await self.send_json({"type": event["event_type"], "message": message})

    async def typing_changed(self, event):
        if event["user_id"] == self.scope["user"].pk:
            return
        await self.send_json(
            {
                "type": "typing.changed",
                "user_id": event["user_id"],
                "is_typing": event["is_typing"],
            }
        )

    async def conversation_read(self, event):
        if event["user_id"] == self.scope["user"].pk:
            return
        await self.send_json(
            {
                "type": "conversation.read",
                "user_id": event["user_id"],
                "message_id": event["message_id"],
                "read_at": event["read_at"],
            }
        )
