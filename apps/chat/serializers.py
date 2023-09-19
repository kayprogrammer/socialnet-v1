import pytz
from rest_framework import serializers
from apps.accounts.models import User
from apps.chat.models import CHAT_TYPES
from apps.common.serializers import SuccessResponseSerializer
from apps.common.file_processors import FileProcessor
from apps.common.validators import validate_image_type
from apps.common.schema_examples import file_upload_data, user_data, latest_message_data


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


class MessageSerializer(serializers.Serializer):
    sender = serializers.SerializerMethodField(default=user_data)
    text = serializers.CharField()
    file = serializers.URLField(source="get_file")
    created_at = serializers.DateTimeField(
        default_timezone=pytz.timezone("UTC"), read_only=True
    )
    updated_at = serializers.DateTimeField(
        default_timezone=pytz.timezone("UTC"), read_only=True
    )

    def get_sender(self, obj) -> dict:
        return get_user(obj.sender)


class MessagesSerializer(serializers.Serializer):
    chat = ChatSerializer()
    messages = MessageSerializer(many=True)
    users = serializers.SerializerMethodField(default=[user_data])

    def get_users(self, obj) -> list:
        return [get_user(user) for user in obj["chat"].recipients]


class ChatsResponseSerializer(SuccessResponseSerializer):
    data = ChatSerializer(many=True)


class ChatResponseSerializer(SuccessResponseSerializer):
    data = MessagesSerializer()


# class ProfileCreateResponseDataSerializer(ProfileSerializer):
#     file_upload_data = serializers.SerializerMethodField(default=file_upload_data)

#     def get_file_upload_data(self, obj) -> dict:
#         image_upload_status = self.context.get("image_upload_status")
#         if image_upload_status:
#             return FileProcessor.generate_file_signature(
#                 key=obj.avatar_id,
#                 folder="avatars",
#             )
#         return None


# class DeleteUserSerializer(serializers.Serializer):
#     password = serializers.CharField()


# class SendFriendRequestSerializer(serializers.Serializer):
#     username = serializers.CharField()


# class AcceptFriendRequestSerializer(SendFriendRequestSerializer):
#     status = serializers.BooleanField()


# # RESPONSE SERIALIZERS
# class ProfilesResponseSerializer(SuccessResponseSerializer):
#     data = ProfileSerializer(many=True)


# class ProfileResponseSerializer(SuccessResponseSerializer):
#     data = ProfileSerializer()


# class ProfileCreateResponseSerializer(SuccessResponseSerializer):
#     data = ProfileCreateResponseDataSerializer()
