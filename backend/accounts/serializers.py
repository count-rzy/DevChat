
from django.contrib.auth.models import User
from rest_framework import serializers

from .models import InviteCode


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=150,
        min_length=3,
    )
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        trim_whitespace=False,
    )
    invite_code = serializers.CharField(
        max_length=32,
        trim_whitespace=True,
    )

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(
                "This username is already taken."
            )
        return value

    def validate_invite_code(self, value):
        if not InviteCode.objects.filter(
            code=value,
            is_used=False,
        ).exists():
            raise serializers.ValidationError(
                "Invalid or already used invite code."
            )
        return value
