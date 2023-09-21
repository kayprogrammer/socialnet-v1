import pytz
from rest_framework import serializers
from apps.chat.models import CHAT_TYPES
from apps.common.serializers import SuccessResponseSerializer
from apps.common.file_processors import FileProcessor
from apps.common.validators import validate_file_type, validate_image_type
from apps.common.schema_examples import file_upload_data, user_data, latest_message_data
from django.utils.translation import gettext_lazy as _


def get_user(user):
    return {
        "name": user.full_name,
        "slug": user.username,
        "avatar": user.get_avatar,
    }


class ChatSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField(max_length=100)
    owner = serializers.SerializerMethodField(default=user_data)
    ctype = serializers.ChoiceField(choices=CHAT_TYPES)
    description = serializers.CharField(max_length=1000)
    image = serializers.CharField(
        source="get_image", default="https://img.url", read_only=True
    )
    latest_message = serializers.SerializerMethodField(default=latest_message_data)
    created_at = serializers.DateTimeField(
        default_timezone=pytz.timezone("UTC"), read_only=True
    )
    updated_at = serializers.DateTimeField(
        default_timezone=pytz.timezone("UTC"), read_only=True
    )

    def get_owner(self, obj) -> dict:
        return get_user(obj.owner)

    def get_latest_message(self, obj) -> dict:
        lmessages = obj.lmessages
        if len(lmessages) > 0:
            message = lmessages[0]
            return {
                "sender": get_user(message.sender),
                "text": message.text,
                "file": message.get_file,
            }
        return None


# For reading and creating messages
class MessageSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    chat_id = serializers.UUIDField(write_only=True, required=False)
    username = serializers.CharField(write_only=True, required=False)
    sender = serializers.SerializerMethodField(default=user_data)
    text = serializers.CharField(required=False)
    file_type = serializers.CharField(
        write_only=True, validators=[validate_file_type], required=False
    )
    file = serializers.URLField(source="get_file", read_only=True)
    created_at = serializers.DateTimeField(
        default_timezone=pytz.timezone("UTC"), read_only=True
    )
    updated_at = serializers.DateTimeField(
        default_timezone=pytz.timezone("UTC"), read_only=True
    )

    def get_sender(self, obj) -> dict:
        return get_user(obj.sender)

    def validate(self, attrs):
        chat_id = attrs.get("chat_id")
        username = attrs.get("username")
        if not chat_id and not username:
            raise serializers.ValidationError(
                {"username": "You must enter the recipient's username"}
            )
        elif chat_id and username:
            raise serializers.ValidationError(
                {"username": "Can't enter username when chat_id is set"}
            )
        if not attrs.get("text") and not attrs.get("file_type"):
            raise serializers.ValidationError({"text": "You must enter a text"})
        return attrs


# Update message serializer
class UpdateMessageSerializer(serializers.Serializer):
    text = serializers.CharField(required=False)
    file_type = serializers.CharField(
        write_only=True, validators=[validate_file_type], required=False
    )

    def validate(self, attrs):
        if not attrs.get("text") and not attrs.get("file_type"):
            raise serializers.ValidationError({"text": "You must enter a text"})
        return attrs


# For a single chat
class MessagesSerializer(serializers.Serializer):
    chat = ChatSerializer()
    messages = MessageSerializer(many=True)
    users = serializers.SerializerMethodField(default=[user_data])

    def get_users(self, obj) -> list:
        return [get_user(user) for user in obj["chat"].recipients]


class UserTouchSerializer(serializers.Serializer):
    username = serializers.CharField()
    action = serializers.ChoiceField(choices=(("ADD", "ADD"), ("REMOVE", "REMOVE")))


class GroupChatSerializer(serializers.Serializer):
    name = serializers.CharField(
        max_length=100, error_messages={"max_length": _("{max_length} characters max.")}
    )
    users_entry = UserTouchSerializer(many=True, write_only=True)
    description = serializers.CharField(
        required=False,
        max_length=1000,
        error_messages={"max_length": _("{max_length} characters max.")},
    )
    file_type = serializers.CharField(
        required=False, validators=[validate_image_type], write_only=True
    )
    image = serializers.CharField(
        source="get_image", default="https://img.url", read_only=True
    )
    users = serializers.SerializerMethodField(default=[user_data])

    def get_users(self, obj) -> list:
        return [get_user(user) for user in obj.recipients]

    def get_fields(self, *args, **kwargs):
        fields = super().get_fields(*args, **kwargs)
        if self.context["request"].method == "POST":
            fields["users_entry"] = serializers.ListField(
                child=serializers.CharField(),
                write_only=True,
                max_length=99,
                error_messages={"max_length": _("{max_length} users max.")},
            )
        return fields


# RESPONSE SERIALIZERS


class ChatsResponseSerializer(SuccessResponseSerializer):
    data = ChatSerializer(many=True)


class ChatResponseSerializer(SuccessResponseSerializer):
    data = MessagesSerializer()


class MessageCreateResponseDataSerializer(MessageSerializer):
    file_upload_data = serializers.SerializerMethodField(default=file_upload_data)

    def get_file_upload_data(self, obj) -> dict:
        file_upload_status = self.context.get("file_upload_status")
        if file_upload_status:
            return FileProcessor.generate_file_signature(
                key=obj.file_id,
                folder="messages",
            )
        return None


class MessageCreateResponseSerializer(SuccessResponseSerializer):
    data = MessageCreateResponseDataSerializer()


class GroupChatCreateResponseDataSerializer(GroupChatSerializer):
    file_upload_data = serializers.SerializerMethodField(default=file_upload_data)

    def get_file_upload_data(self, obj) -> dict:
        file_upload_status = self.context.get("file_upload_status")
        if file_upload_status:
            return FileProcessor.generate_file_signature(
                key=obj.file_id,
                folder="groups",
            )
        return None


class GroupChatCreateResponseSerializer(SuccessResponseSerializer):
    data = GroupChatCreateResponseDataSerializer()
