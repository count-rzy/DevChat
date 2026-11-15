from django.urls import path

from .views import (
    conversation_detail,
    conversation_messages,
    conversations,
    message_detail,
    mark_conversation_read,
    toggle_message_reaction,
)


urlpatterns = [
    path("", conversations, name="conversations"),
    path("<int:conversation_id>/", conversation_detail, name="conversation-detail"),
    path(
        "<int:conversation_id>/messages/",
        conversation_messages,
        name="conversation-messages",
    ),
    path(
        "<int:conversation_id>/messages/<int:message_id>/",
        message_detail,
        name="message-detail",
    ),
    path(
        "<int:conversation_id>/messages/<int:message_id>/reactions/",
        toggle_message_reaction,
        name="message-reactions",
    ),
    path(
        "<int:conversation_id>/read/",
        mark_conversation_read,
        name="conversation-read",
    ),
]
