import json
import logging
import warnings
from io import BytesIO
from json import JSONDecodeError

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.db import IntegrityError, transaction
from django.http import FileResponse, Http404, JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from PIL import Image, UnidentifiedImageError

from .models import InviteCode, UserProfile
from .serializers import LoginSerializer, ProfileUpdateSerializer, RegisterSerializer
from .throttling import (
    login_ip_identity,
    login_user_identity,
    rate_limit,
    registration_identity,
)

logger = logging.getLogger(__name__)
MAX_AVATAR_SIZE = 5 * 1024 * 1024
MAX_AVATAR_PIXELS = 20_000_000
ALLOWED_AVATAR_FORMATS = {"JPEG", "PNG", "WEBP"}


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
        "avatar_url": (
            f"/api/accounts/users/{profile.user_id}/avatar/"
            if profile.avatar
            else None
        ),
    }


def _normalized_avatar(uploaded_file):
    if uploaded_file.size > MAX_AVATAR_SIZE:
        raise ValueError("Avatar file exceeds the 5 MB limit.")

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(uploaded_file) as image:
                if image.format not in ALLOWED_AVATAR_FORMATS:
                    raise ValueError("Use a JPEG, PNG, or WebP image.")
                if image.width * image.height > MAX_AVATAR_PIXELS:
                    raise ValueError("Avatar dimensions are too large.")
                if getattr(image, "n_frames", 1) != 1:
                    raise ValueError("Animated images are not supported.")
                image.load()
                has_alpha = "A" in image.getbands() or "transparency" in image.info
                normalized = image.convert("RGBA" if has_alpha else "RGB")
                normalized.thumbnail((512, 512))
                output = BytesIO()
                normalized.save(output, format="WEBP", quality=85, method=6)
                return ContentFile(output.getvalue(), name="avatar.webp")
    except ValueError:
        raise
    except (Image.DecompressionBombError, Image.DecompressionBombWarning,
            UnidentifiedImageError, OSError) as error:
        raise ValueError("The uploaded file is not a valid supported image.") from error


def _delete_avatar_file(storage, name):
    try:
        storage.delete(name)
    except Exception:
        logger.exception("Could not remove obsolete avatar file")


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


@csrf_protect
@require_http_methods(["POST", "DELETE"])
def manage_my_avatar(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"detail": "Authentication credentials were not provided."},
            status=401,
        )

    if request.method == "POST":
        uploaded_file = request.FILES.get("avatar")
        if uploaded_file is None:
            return JsonResponse({"avatar": ["Choose an image file."]}, status=400)
        try:
            content = _normalized_avatar(uploaded_file)
        except ValueError as error:
            return JsonResponse({"avatar": [str(error)]}, status=400)

    new_name = None
    try:
        with transaction.atomic():
            profile, _ = UserProfile.objects.select_for_update().get_or_create(
                user=request.user,
            )
            old_name = profile.avatar.name if profile.avatar else None
            storage = profile.avatar.storage
            if request.method == "DELETE":
                if old_name:
                    profile.avatar = None
                    profile.save(update_fields=["avatar"])
                    transaction.on_commit(
                        lambda: _delete_avatar_file(storage, old_name)
                    )
            else:
                profile.avatar.save("avatar.webp", content, save=False)
                new_name = profile.avatar.name
                profile.save(update_fields=["avatar"])
                if old_name and old_name != new_name:
                    transaction.on_commit(
                        lambda: _delete_avatar_file(storage, old_name)
                    )
    except Exception:
        if new_name:
            _delete_avatar_file(storage, new_name)
        raise

    return JsonResponse({
        "profile": {
            **_public_profile(profile),
            "preferred_language": profile.preferred_language,
            "date_joined": request.user.date_joined.isoformat(),
        }
    })


@require_GET
def user_avatar(request, user_id):
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
    if not profile.avatar:
        raise Http404

    response = FileResponse(profile.avatar.open("rb"), content_type="image/webp")
    response["Cache-Control"] = "private, no-store"
    return response


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
