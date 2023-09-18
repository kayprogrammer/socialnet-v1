import pytz
from rest_framework import serializers
from apps.accounts.models import User
from apps.chat.models import CHAT_TYPES
from apps.common.serializers import SuccessResponseSerializer
from apps.common.file_processors import FileProcessor
from apps.common.validators import validate_image_type
from apps.common.schema_examples import file_upload_data


def get_user(user):
    return {
        "name": user.full_name,
        "slug": user.username,
        "avatar": user.get_avatar,
    }


class ChatSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    owner = serializers.SerializerMethodField()
    ctype = serializers.ChoiceField(choices=CHAT_TYPES)
    description = serializers.CharField(max_length=1000)
    image = serializers.CharField(
        source="get_image", default="https://img.url", read_only=True
    )
    # latest_message = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(
        default_timezone=pytz.timezone("UTC"), read_only=True
    )
    updated_at = serializers.DateTimeField(
        default_timezone=pytz.timezone("UTC"), read_only=True
    )

    def get_owner(self, obj):
        return get_user(obj.owner)

    def get_latest_message(self, obj) -> dict:
        message = obj.latest_message
        print(message)
        if message:
            return {
                "sender": get_user(message.sender),
                "text": message.text,
                "file": message.get_file,
            }
        return None


class ChatDetailSerializer(ChatSerializer):
    users = serializers.SerializerMethodField()

    def get_users(self, obj) -> list:
        return [get_user(user) for user in obj.users.all()]


class MessageSerializer(serializers.Serializer):
    chat = ChatSerializer()
    sender = serializers.SerializerMethodField()
    text = serializers.CharField()
    file = serializers.URLField(source="get_file")
    created_at = serializers.DateTimeField(
        default_timezone=pytz.timezone("UTC"), read_only=True
    )
    updated_at = serializers.DateTimeField(
        default_timezone=pytz.timezone("UTC"), read_only=True
    )

    def get_sender(self, obj):
        return get_user(obj.sender)


class ChatsResponseSerializer(SuccessResponseSerializer):
    data = ChatSerializer(many=True)


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
