from rest_framework import serializers


class CreateConversationSerializer(serializers.Serializer):
    other_user_id = serializers.IntegerField(min_value=1)


class CreateMessageSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=4000, trim_whitespace=True)

    def validate_content(self, value):
        content = value.strip()
        if not content:
            raise serializers.ValidationError("Message cannot be blank.")
        return content
