
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import InviteCode


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=150,
        min_length=3,
        validators=[UnicodeUsernameValidator()],
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

    def validate_password(self, value):
        username = self.initial_data.get("username", "")
        user = User(username=username if isinstance(username, str) else "")
        try:
            validate_password(value, user=user)
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.messages) from error
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
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


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, trim_whitespace=True)
    password = serializers.CharField(write_only=True, trim_whitespace=False)
