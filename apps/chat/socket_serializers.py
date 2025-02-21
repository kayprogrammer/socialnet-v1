from rest_framework import serializers

MESSAGE_STATUS = (
    ("CREATED", "CREATED"),
    ("UPDATED", "UPDATED"),
    ("DELETED", "DELETED"),
)


class SocketMessageSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=MESSAGE_STATUS)
    id = serializers.UUIDField()
