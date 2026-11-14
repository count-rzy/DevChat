import hashlib
from functools import wraps

from django.core.cache import cache
from django.http import JsonResponse


def _client_ip(request):
    # REMOTE_ADDR is controlled by the server socket. Do not trust forwarded
    # headers unless the deployment explicitly validates its proxy chain.
    return request.META.get("REMOTE_ADDR", "unknown")


def rate_limit(*, scope, limit, window, identity):
    """Apply a short fixed-window request limit using Django's configured cache."""

    def decorate(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            value = str(identity(request))
            digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
            key = f"devchat:auth-limit:{scope}:{digest}"

            if not cache.add(key, 1, timeout=window):
                try:
                    attempts = cache.incr(key)
                except ValueError:
                    # The key may expire between add() and incr().
                    cache.add(key, 1, timeout=window)
                    attempts = cache.get(key, 1)
                if attempts > limit:
                    return JsonResponse(
                        {"detail": "Too many requests. Please try again later."},
                        status=429,
                        headers={"Retry-After": str(window)},
                    )
            return view(request, *args, **kwargs)

        return wrapped

    return decorate


def login_ip_identity(request):
    return _client_ip(request)


def login_user_identity(request):
    username = ""
    try:
        import json

        payload = json.loads(request.body)
        if isinstance(payload, dict) and isinstance(payload.get("username"), str):
            username = payload["username"].strip().casefold()
    except (UnicodeDecodeError, ValueError):
        pass
    return f"{_client_ip(request)}:{username}"


def registration_identity(request):
    return _client_ip(request)
