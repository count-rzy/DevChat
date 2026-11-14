from django.urls import path

from .views import conversation_detail, conversation_messages, conversations


urlpatterns = [
    path("", conversations, name="conversations"),
    path("<int:conversation_id>/", conversation_detail, name="conversation-detail"),
    path(
        "<int:conversation_id>/messages/",
        conversation_messages,
        name="conversation-messages",
    ),
]
