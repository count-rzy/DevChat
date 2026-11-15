from rest_framework import serializers
ALLOWED_REACTIONS = ["👍", "❤️", "😂", "😮", "😢"]


def message_payload(message, viewer_id=None):
    profile = getattr(message.sender, "profile", None)
    reply = message.reply_to if message.reply_to_id else None
    reactions = {}
    for reaction in message.reactions.all():
        row = reactions.setdefault(
            reaction.emoji,
            {"emoji": reaction.emoji, "count": 0, "reacted": False},
        )
        row["count"] += 1
        if reaction.user_id == viewer_id:
            row["reacted"] = True
    return {
        "id": message.pk,
        "sender": {
            "id": message.sender_id,
            "username": message.sender.get_username(),
            "display_name": (profile.display_name if profile else "")
            or message.sender.get_username(),
        },
        "content": message.content,
        "created_at": message.created_at.isoformat(),
        "edited_at": message.edited_at.isoformat() if message.edited_at else None,
        "deleted_at": message.deleted_at.isoformat() if message.deleted_at else None,
        "reply_to": (
            {
                "id": reply.pk,
                "sender_name": (reply.sender.profile.display_name
                                if hasattr(reply.sender, "profile") else "")
                or reply.sender.get_username(),
                "content": None if reply.deleted_at else reply.content,
                "deleted": reply.deleted_at is not None,
            }
            if reply
            else None
        ),
        "reactions": list(reactions.values()),
    }


class CreateConversationSerializer(serializers.Serializer):
    other_user_id = serializers.IntegerField(min_value=1)


class CreateMessageSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=4000, trim_whitespace=True)
    reply_to_id = serializers.IntegerField(min_value=1, required=False)

    def validate_content(self, value):
        content = value.strip()
        if not content:
            raise serializers.ValidationError("Message cannot be blank.")
        return content


class EditMessageSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=4000, trim_whitespace=True)

    def validate_content(self, value):
        content = value.strip()
        if not content:
            raise serializers.ValidationError("Message cannot be blank.")
        return content


class MessageReactionSerializer(serializers.Serializer):
    emoji = serializers.ChoiceField(choices=ALLOWED_REACTIONS)
