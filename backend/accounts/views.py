
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import InviteCode
from .serializers import RegisterSerializer


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

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
        return Response(
            {"invite_code": ["Invalid or already used invite code."]},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except IntegrityError:
        return Response(
            {"username": ["This username is already taken."]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        {
            "message": "Account created successfully.",
            "user": {
                "id": user.id,
                "username": user.username,
            },
        },
        status=status.HTTP_201_CREATED,
    )
