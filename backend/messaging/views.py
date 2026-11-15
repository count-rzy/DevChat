import json
from json import JSONDecodeError

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .models import Conversation, ConversationReadState, Message, MessageReaction
from .events import publish_message, publish_read_state
from .serializers import (
    CreateConversationSerializer,
    CreateMessageSerializer,
    EditMessageSerializer,
    MessageReactionSerializer,
    message_payload,
)

User = get_user_model()
MESSAGE_PAGE_SIZE = 100


def _json_object(request):
    try:
        data = json.loads(request.body)
    except (JSONDecodeError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _authenticated_or_response(request):
    if request.user.is_authenticated:
        return None
    return JsonResponse(
        {"detail": "Authentication credentials were not provided."},
        status=401,
    )


def _public_user(user):
    profile = getattr(user, "profile", None)
    return {
        "id": user.pk,
        "username": user.get_username(),
        "display_name": (profile.display_name if profile else "") or user.get_username(),
        "avatar_url": (
            f"/api/accounts/users/{user.pk}/avatar/"
            if profile and profile.avatar
            else None
        ),
    }


def _conversation_for_member(request, conversation_id):
    try:
        return Conversation.objects.select_related("member_one", "member_two").get(
            pk=conversation_id,
        )
    except Conversation.DoesNotExist as error:
        raise Http404 from error


def _conversation_payload(conversation, user):
    other_user = (
        conversation.member_two
        if conversation.member_one_id == user.pk
        else conversation.member_one
    )
    last_message = conversation.messages.order_by("-created_at", "-pk").first()
    own_read_state = conversation.read_states.filter(user=user).first()
    other_read_state = conversation.read_states.exclude(user=user).first()
    unread = conversation.messages.exclude(sender=user)
    if own_read_state:
        unread = unread.filter(pk__gt=own_read_state.last_read_message_id)
    return {
        "id": conversation.pk,
        "other_user": _public_user(other_user),
        "last_message": (
            {
                "id": last_message.pk,
                "content": last_message.content,
                "sender_id": last_message.sender_id,
                "created_at": last_message.created_at.isoformat(),
                "is_deleted": last_message.deleted_at is not None,
            }
            if last_message
            else None
        ),
        "unread_count": unread.count(),
        "other_last_read_message_id": (
            other_read_state.last_read_message_id if other_read_state else None
        ),
        "created_at": conversation.created_at.isoformat(),
    }


def _message_payload(message, viewer_id=None):
    return message_payload(message, viewer_id=viewer_id)


@csrf_protect
@require_http_methods(["GET", "POST"])
def conversations(request):
    denied = _authenticated_or_response(request)
    if denied:
        return denied

    if request.method == "GET":
        rows = Conversation.objects.filter(
            Q(member_one_id=request.user.pk) | Q(member_two_id=request.user.pk)
        ).select_related("member_one", "member_two")
        return JsonResponse({
            "conversations": [
                _conversation_payload(row, request.user) for row in rows
            ]
        })

    data = _json_object(request)
    if data is None:
        return JsonResponse({"detail": "Request body must be a JSON object."}, status=400)
    serializer = CreateConversationSerializer(data=data)
    if not serializer.is_valid():
        return JsonResponse(serializer.errors, status=400)
    other_id = serializer.validated_data["other_user_id"]
    if other_id == request.user.pk:
        return JsonResponse({"other_user_id": ["A conversation with yourself is not allowed."]}, status=400)
    try:
        other_user = User.objects.get(pk=other_id, is_active=True)
    except User.DoesNotExist:
        return JsonResponse({"other_user_id": ["User not found."]}, status=404)

    member_one, member_two = sorted((request.user, other_user), key=lambda user: user.pk)
    try:
        with transaction.atomic():
            conversation, created = Conversation.objects.get_or_create(
                member_one=member_one,
                member_two=member_two,
            )
    except IntegrityError:
        # A concurrent request may have inserted the same unique pair.
        conversation = Conversation.objects.get(
            member_one=member_one,
            member_two=member_two,
        )
    return JsonResponse(
        {"conversation": _conversation_payload(conversation, request.user)},
        status=201 if created else 200,
    )


@require_GET
def conversation_detail(request, conversation_id):
    denied = _authenticated_or_response(request)
    if denied:
        return denied
    conversation = _conversation_for_member(request, conversation_id)
    if not conversation.includes(request.user):
        raise Http404
    return JsonResponse({"conversation": _conversation_payload(conversation, request.user)})


@csrf_protect
@require_http_methods(["GET", "POST"])
def conversation_messages(request, conversation_id):
    denied = _authenticated_or_response(request)
    if denied:
        return denied
    conversation = _conversation_for_member(request, conversation_id)
    if not conversation.includes(request.user):
        raise Http404

    if request.method == "GET":
        before = request.GET.get("before")
        queryset = conversation.messages.select_related(
            "sender__profile",
            "reply_to__sender__profile",
        ).prefetch_related("reactions__user")
        if before:
            try:
                before_id = int(before)
            except ValueError:
                return JsonResponse({"before": ["Use a message ID cursor."]}, status=400)
            if before_id < 1:
                return JsonResponse({"before": ["Use a positive message ID cursor."]}, status=400)
            queryset = queryset.filter(pk__lt=before_id)
        page = list(queryset.order_by("-created_at", "-pk")[:MESSAGE_PAGE_SIZE])
        return JsonResponse({
            "messages": [
                message_payload(message, viewer_id=request.user.pk)
                for message in reversed(page)
            ],
            "next_before": page[-1].pk if len(page) == MESSAGE_PAGE_SIZE else None,
        })

    data = _json_object(request)
    if data is None:
        return JsonResponse({"detail": "Request body must be a JSON object."}, status=400)
    serializer = CreateMessageSerializer(data=data)
    if not serializer.is_valid():
        return JsonResponse(serializer.errors, status=400)
    reply_to = None
    reply_to_id = serializer.validated_data.get("reply_to_id")
    if reply_to_id is not None:
        try:
            reply_to = Message.objects.select_related(
                "sender__profile",
            ).get(pk=reply_to_id, conversation=conversation)
        except Message.DoesNotExist as error:
            raise Http404 from error
    with transaction.atomic():
        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=serializer.validated_data["content"],
            reply_to=reply_to,
        )
        conversation.save(update_fields=["updated_at"])
    publish_message(conversation.pk, message.pk)
    return JsonResponse({
        "message": message_payload(message, viewer_id=request.user.pk)
    }, status=201)


@csrf_protect
@require_http_methods(["PATCH", "DELETE"])
def message_detail(request, conversation_id, message_id):
    denied = _authenticated_or_response(request)
    if denied:
        return denied
    conversation = _conversation_for_member(request, conversation_id)
    if not conversation.includes(request.user):
        raise Http404
    try:
        message = Message.objects.select_related("sender").get(
            pk=message_id,
            conversation=conversation,
        )
    except Message.DoesNotExist as error:
        raise Http404 from error
    if message.sender_id != request.user.pk:
        return JsonResponse({"detail": "You can only change your own messages."}, status=403)

    if request.method == "PATCH":
        if message.deleted_at:
            return JsonResponse({"detail": "Deleted messages cannot be edited."}, status=400)
        data = _json_object(request)
        if data is None:
            return JsonResponse({"detail": "Request body must be a JSON object."}, status=400)
        serializer = EditMessageSerializer(data=data)
        if not serializer.is_valid():
            return JsonResponse(serializer.errors, status=400)
        with transaction.atomic():
            message = Message.objects.select_for_update().get(pk=message.pk)
            if message.deleted_at:
                return JsonResponse({"detail": "Deleted messages cannot be edited."}, status=400)
            message.content = serializer.validated_data["content"]
            message.edited_at = timezone.now()
            message.save(update_fields=["content", "edited_at"])
        event_type = "message.updated"
    else:
        if message.deleted_at:
            return JsonResponse({
                "message": message_payload(message, viewer_id=request.user.pk),
            })
        with transaction.atomic():
            message = Message.objects.select_for_update().get(pk=message.pk)
            if not message.deleted_at:
                message.content = ""
                message.deleted_at = timezone.now()
                message.save(update_fields=["content", "deleted_at"])
                message.reactions.all().delete()
        event_type = "message.updated"

    message = Message.objects.select_related(
        "sender__profile",
        "reply_to__sender__profile",
    ).prefetch_related("reactions__user").get(pk=message.pk)
    publish_message(conversation.pk, message.pk, event_type=event_type)
    return JsonResponse({
        "message": message_payload(message, viewer_id=request.user.pk),
    })


@csrf_protect
@require_POST
def toggle_message_reaction(request, conversation_id, message_id):
    denied = _authenticated_or_response(request)
    if denied:
        return denied
    conversation = _conversation_for_member(request, conversation_id)
    if not conversation.includes(request.user):
        raise Http404

    data = _json_object(request)
    if data is None:
        return JsonResponse({"detail": "Request body must be a JSON object."}, status=400)
    serializer = MessageReactionSerializer(data=data)
    if not serializer.is_valid():
        return JsonResponse(serializer.errors, status=400)
    try:
        with transaction.atomic():
            message = Message.objects.select_for_update().get(
                pk=message_id,
                conversation=conversation,
            )
            if message.deleted_at:
                return JsonResponse({"detail": "Deleted messages cannot be reacted to."}, status=400)
            reaction, created = MessageReaction.objects.get_or_create(
                message=message,
                user=request.user,
                emoji=serializer.validated_data["emoji"],
            )
            if not created:
                reaction.delete()
    except Message.DoesNotExist as error:
        raise Http404 from error

    message = Message.objects.select_related(
        "sender__profile",
        "reply_to__sender__profile",
    ).prefetch_related("reactions__user").get(pk=message.pk)
    publish_message(conversation.pk, message.pk, event_type="message.updated")
    return JsonResponse({
        "message": message_payload(message, viewer_id=request.user.pk),
    })


@csrf_protect
@require_POST
def mark_conversation_read(request, conversation_id):
    denied = _authenticated_or_response(request)
    if denied:
        return denied
    conversation = _conversation_for_member(request, conversation_id)
    if not conversation.includes(request.user):
        raise Http404
    data = _json_object(request)
    if data is None or not isinstance(data.get("message_id"), int):
        return JsonResponse({"message_id": ["A message ID is required."]}, status=400)
    try:
        message = conversation.messages.get(pk=data["message_id"])
    except Message.DoesNotExist as error:
        raise Http404 from error
    with transaction.atomic():
        state, created = ConversationReadState.objects.select_for_update().get_or_create(
            conversation=conversation,
            user=request.user,
            defaults={"last_read_message": message},
        )
        if not created and message.pk > state.last_read_message_id:
            state.last_read_message = message
            state.save(update_fields=["last_read_message", "read_at"])
    state.refresh_from_db()
    publish_read_state(
        conversation.pk,
        request.user.pk,
        state.last_read_message_id,
        state.read_at,
    )
    return JsonResponse({"conversation": _conversation_payload(conversation, request.user)})
