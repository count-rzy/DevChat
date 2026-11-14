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
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .models import InviteCode, UserProfile
from .serializers import LoginSerializer, ProfileUpdateSerializer, RegisterSerializer
from .throttling import (
    login_ip_identity,
    login_user_identity,
    rate_limit,
    registration_identity,
)


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


def _public_profile(profile):
    return {
        "id": profile.user_id,
        "username": profile.user.get_username(),
        "display_name": profile.display_name or profile.user.get_username(),
        "description": profile.description,
    }


def _request_user_profile(request):
    return UserProfile.objects.get_or_create(user=request.user)[0]


def csrf_failure(request, reason=""):
    return JsonResponse({"detail": "CSRF verification failed."}, status=403)


@require_GET
@ensure_csrf_cookie
def csrf_token(request):
    return JsonResponse({"csrfToken": get_token(request)})


@csrf_protect
@require_POST
@rate_limit(scope="register-ip", limit=5, window=3600, identity=registration_identity)
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
@rate_limit(scope="login-ip", limit=30, window=60, identity=login_ip_identity)
@rate_limit(scope="login-user", limit=10, window=60, identity=login_user_identity)
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


@require_GET
def my_profile(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"detail": "Authentication credentials were not provided."},
            status=401,
        )
    profile = _request_user_profile(request)
    return JsonResponse({
        "profile": {
            **_public_profile(profile),
            "preferred_language": profile.preferred_language,
            "date_joined": request.user.date_joined.isoformat(),
        }
    })


@csrf_protect
@require_http_methods(["PATCH"])
def update_my_profile(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"detail": "Authentication credentials were not provided."},
            status=401,
        )
    data = _json_object(request)
    if data is None:
        return JsonResponse(
            {"detail": "Request body must be a JSON object."},
            status=400,
        )
    profile = _request_user_profile(request)
    serializer = ProfileUpdateSerializer(profile, data=data, partial=True)
    if not serializer.is_valid():
        return JsonResponse(serializer.errors, status=400)
    serializer.save()
    return JsonResponse({"profile": {
        **_public_profile(profile),
        "preferred_language": profile.preferred_language,
        "date_joined": request.user.date_joined.isoformat(),
    }})


@require_GET
def public_profiles(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"detail": "Authentication credentials were not provided."},
            status=401,
        )
    profiles = UserProfile.objects.filter(user__is_active=True).exclude(
        user=request.user
    ).select_related("user").order_by("user__username")
    return JsonResponse({"users": [_public_profile(profile) for profile in profiles]})


@require_GET
def public_profile(request, user_id):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"detail": "Authentication credentials were not provided."},
            status=401,
        )
    try:
        profile = UserProfile.objects.select_related("user").get(
            user_id=user_id,
            user__is_active=True,
        )
    except UserProfile.DoesNotExist as error:
        raise Http404 from error
    return JsonResponse({"profile": _public_profile(profile)})
