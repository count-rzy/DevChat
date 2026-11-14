import json
from json import JSONDecodeError

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .models import Conversation, Message
from .serializers import CreateConversationSerializer, CreateMessageSerializer

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
    return {
        "id": conversation.pk,
        "other_user": _public_user(other_user),
        "last_message": (
            {
                "content": last_message.content,
                "sender_id": last_message.sender_id,
                "created_at": last_message.created_at.isoformat(),
            }
            if last_message
            else None
        ),
        "created_at": conversation.created_at.isoformat(),
    }


def _message_payload(message):
    return {
        "id": message.pk,
        "sender": _public_user(message.sender),
        "content": message.content,
        "created_at": message.created_at.isoformat(),
    }


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
        queryset = conversation.messages.select_related("sender")
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
            "messages": [_message_payload(message) for message in reversed(page)],
            "next_before": page[-1].pk if len(page) == MESSAGE_PAGE_SIZE else None,
        })

    data = _json_object(request)
    if data is None:
        return JsonResponse({"detail": "Request body must be a JSON object."}, status=400)
    serializer = CreateMessageSerializer(data=data)
    if not serializer.is_valid():
        return JsonResponse(serializer.errors, status=400)
    with transaction.atomic():
        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=serializer.validated_data["content"],
        )
        conversation.save(update_fields=["updated_at"])
    return JsonResponse({"message": _message_payload(message)}, status=201)
