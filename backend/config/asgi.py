"""ASGI config for the DevChat project."""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import OriginValidator
from django.conf import settings
from django.core.asgi import get_asgi_application
from django.urls import path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Initialize Django before importing modules that may load models.
django_asgi_app = get_asgi_application()

from messaging.consumers import ConversationConsumer  # noqa: E402

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": OriginValidator(
            AuthMiddlewareStack(
                URLRouter(
                    [
                        path(
                            "ws/conversations/<int:conversation_id>/",
                            ConversationConsumer.as_asgi(),
                        ),
                    ]
                )
            ),
            settings.CSRF_TRUSTED_ORIGINS,
        ),
    }
)
