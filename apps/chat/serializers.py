import pytz
from rest_framework import serializers
from apps.chat.models import CHAT_TYPES
from apps.chat.utils import handle_lerrors, get_user
from apps.common.serializers import (
    PaginatedResponseDataSerializer,
    SuccessResponseSerializer,
)
from apps.common.file_processors import FileProcessor
from apps.common.validators import validate_file_type, validate_image_type
from apps.common.schema_examples import file_upload_data, user_data, latest_message_data
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError


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
    chat_id = serializers.UUIDField(required=False)
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
class MessagesResponseDataSchema(PaginatedResponseDataSerializer):
    items = MessageSerializer(many=True)


class MessagesSerializer(serializers.Serializer):
    chat = ChatSerializer()
    messages = MessagesResponseDataSchema()
    users = serializers.SerializerMethodField(default=[user_data])

    def get_users(self, obj) -> list:
        return [get_user(user) for user in obj["chat"].recipients]


username_field = serializers.ListField(
    child=serializers.CharField(
        error_messages={"invalid": _("One of the usernames is an invalid string")}
    ),
    write_only=True,
    min_length=1,
    max_length=99,
    error_messages={
        "max_length": _("{max_length} users max."),
        "min_length": _("{min_length} users min."),
    },
)


class GroupChatSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(
        max_length=100, error_messages={"max_length": _("{max_length} characters max.")}
    )
    usernames_to_add = username_field
    usernames_to_remove = username_field
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
            fields.pop("usernames_to_remove")
        return fields

    def to_internal_value(self, data):
        try:
            return super().to_internal_value(data)
        except ValidationError as exc:
            err = exc.detail
            errors = handle_lerrors(err)
            if len(errors) > 0:
                raise serializers.ValidationError(errors)
            raise

    def validate(self, attrs):
        usernames_to_add = attrs.get("usernames_to_add")
        usernames_to_remove = attrs.get("usernames_to_remove")
        if usernames_to_add and usernames_to_remove:
            # Convert lists to sets and check for intersection
            intersection = set(usernames_to_add) & set(usernames_to_remove)
            if intersection:
                raise serializers.ValidationError(
                    {
                        "usernames_to_remove": "Must not have any matching items with usernames to add"
                    }
                )
        return attrs


# RESPONSE SERIALIZERS


class ChatsResponseDataSerializer(PaginatedResponseDataSerializer):
    chats = ChatSerializer(many=True, source="items")


class ChatsResponseSerializer(SuccessResponseSerializer):
    data = ChatsResponseDataSerializer()


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
                key=obj.image_id,
                folder="groups",
            )
        return None


class GroupChatCreateResponseSerializer(SuccessResponseSerializer):
    data = GroupChatCreateResponseDataSerializer()
