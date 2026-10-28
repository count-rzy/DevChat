import json
from json import JSONDecodeError

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.conf import settings
from django.db import IntegrityError, transaction
from django.http import Http404, JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .models import InviteCode
from .serializers import LoginSerializer, RegisterSerializer


def dev_registration_page(request):
    if not settings.DEBUG:
        raise Http404
    return render(request, "accounts/dev_registration.html")


def _json_object(request):
    try:
        data = json.loads(request.body)
    except (JSONDecodeError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _public_user(user):
    return {"id": user.pk, "username": user.get_username()}


def csrf_failure(request, reason=""):
    return JsonResponse({"detail": "CSRF verification failed."}, status=403)


@require_GET
@ensure_csrf_cookie
def csrf_token(request):
    return JsonResponse({"csrfToken": get_token(request)})


@csrf_protect
@require_POST
def register(request):
    data = _json_object(request)
    if data is None:
        return JsonResponse(
            {"detail": "Request body must be a JSON object."},
            status=400,
        )

    serializer = RegisterSerializer(data=data)
    if not serializer.is_valid():
        return JsonResponse(serializer.errors, status=400)

    username = serializer.validated_data["username"]
    password = serializer.validated_data["password"]
    invite_code = serializer.validated_data["invite_code"]

    try:
        with transaction.atomic():
            invite = InviteCode.objects.select_for_update().get(
                code=invite_code,
                is_used=False,
            )

            user = User.objects.create_user(
                username=username,
                password=password,
            )

            invite.is_used = True
            invite.save(update_fields=["is_used"])
    except InviteCode.DoesNotExist:
        return JsonResponse(
            {"invite_code": ["Invalid or already used invite code."]},
            status=400,
        )
    except IntegrityError:
        if User.objects.filter(username=username).exists():
            return JsonResponse(
                {"username": ["This username is already taken."]},
                status=400,
            )
        raise

    return JsonResponse(
        {
            "message": "Account created successfully.",
            "user": _public_user(user),
        },
        status=201,
    )


@csrf_protect
@require_POST
def log_in(request):
    data = _json_object(request)
    if data is None:
        return JsonResponse(
            {"detail": "Request body must be a JSON object."},
            status=400,
        )

    serializer = LoginSerializer(data=data)
    if not serializer.is_valid():
        return JsonResponse(serializer.errors, status=400)

    user = authenticate(
        request,
        username=serializer.validated_data["username"],
        password=serializer.validated_data["password"],
    )
    if user is None:
        return JsonResponse(
            {"detail": "Invalid username or password."},
            status=401,
        )

    login(request, user)
    return JsonResponse({"user": _public_user(user)})


@csrf_protect
@require_POST
def log_out(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"detail": "Authentication credentials were not provided."},
            status=401,
        )

    logout(request)
    return JsonResponse({"detail": "Logged out."})


@require_GET
def current_user(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"detail": "Authentication credentials were not provided."},
            status=401,
        )

    return JsonResponse({"user": _public_user(request.user)})
