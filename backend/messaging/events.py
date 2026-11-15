import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


def conversation_group_name(conversation_id):
    return f"conversation_{conversation_id}"


def publish_message(conversation_id, message_id, event_type="message.created"):
    """Broadcast a persisted message without making the HTTP send depend on WS."""
    try:
        channel_layer = get_channel_layer()
        if channel_layer is None:
            return
        async_to_sync(channel_layer.group_send)(
            conversation_group_name(conversation_id),
            {
                "type": "message.event",
                "event_type": event_type,
                "message_id": message_id,
            },
        )
    except Exception:
        # The message is already durable. Clients reconcile through the history API.
        logger.exception("Could not publish realtime event for conversation %s", conversation_id)


def publish_read_state(conversation_id, user_id, message_id, read_at):
    try:
        channel_layer = get_channel_layer()
        if channel_layer is None:
            return
        async_to_sync(channel_layer.group_send)(
            conversation_group_name(conversation_id),
            {
                "type": "conversation.read",
                "user_id": user_id,
                "message_id": message_id,
                "read_at": read_at.isoformat(),
            },
        )
    except Exception:
        logger.exception("Could not publish read state for conversation %s", conversation_id)
