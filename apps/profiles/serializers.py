import pytz
from rest_framework import serializers
from apps.common.serializers import SuccessResponseSerializer
from apps.common.file_processors import FileProcessor
from apps.common.validators import validate_image_type
from apps.common.schema_examples import file_upload_data, user_data
from apps.profiles.models import NOTIFICATION_TYPE_CHOICES


def get_user(user):
    return {
        "name": user.full_name,
        "slug": user.username,
        "avatar": user.get_avatar,
    }


class CitySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    region = serializers.CharField(source="region.name")
    country = serializers.CharField(source="country.name")


class CitiesResponseSerializer(SuccessResponseSerializer):
    data = CitySerializer(many=True)


class ProfileSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=50)
    last_name = serializers.CharField(max_length=50)
    username = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    avatar = serializers.CharField(
        source="get_avatar", default="https://img.url", read_only=True
    )
    bio = serializers.CharField(max_length=200)
    dob = serializers.DateField()
    city = serializers.CharField(source="city.name", allow_null=True, read_only=True)
    city_id = serializers.IntegerField(write_only=True)
    created_at = serializers.DateTimeField(
        default_timezone=pytz.timezone("UTC"), read_only=True
    )
    updated_at = serializers.DateTimeField(
        default_timezone=pytz.timezone("UTC"), read_only=True
    )
    file_type = serializers.CharField(validators=[validate_image_type], write_only=True)


class ProfileCreateResponseDataSerializer(ProfileSerializer):
    file_upload_data = serializers.SerializerMethodField(default=file_upload_data)

    def get_file_upload_data(self, obj) -> dict:
        image_upload_status = self.context.get("image_upload_status")
        if image_upload_status:
            return FileProcessor.generate_file_signature(
                key=obj.avatar_id,
                folder="avatars",
            )
        return None


class DeleteUserSerializer(serializers.Serializer):
    password = serializers.CharField()


class SendFriendRequestSerializer(serializers.Serializer):
    username = serializers.CharField()


class AcceptFriendRequestSerializer(SendFriendRequestSerializer):
    status = serializers.BooleanField()


async def async_check_is_read(instance, user_id):
    if await instance.read_by.filter(id=user_id).aexists():
        return True
    return False


class NotificationSerializer(serializers.Serializer):
    sender = serializers.SerializerMethodField(default=user_data)
    ntype = serializers.ChoiceField(choices=NOTIFICATION_TYPE_CHOICES)
    message = serializers.CharField(default="John Doe reacted to your post")
    post_slug = serializers.CharField(
        default="john-doe-d23dde64-a242-4ed0-bd75-4c759624b3a6"
    )
    comment_slug = serializers.CharField(
        default="john-doe-a23dde64-a242-4ed0-bd75-4c759624b3a9"
    )
    reply_slug = serializers.CharField(
        default="john-doe-a45dde64-a242-4ed0-bd75-4c759624b3a1"
    )
    is_read = serializers.BooleanField(default=False)

    def get_sender(self, obj) -> dict:
        sender = obj.sender
        return get_user(sender) if sender else None


# RESPONSE SERIALIZERS
class ProfilesResponseSerializer(SuccessResponseSerializer):
    data = ProfileSerializer(many=True)


class ProfileResponseSerializer(SuccessResponseSerializer):
    data = ProfileSerializer()


class ProfileCreateResponseSerializer(SuccessResponseSerializer):
    data = ProfileCreateResponseDataSerializer()


class NotificationsResponseSerializer(SuccessResponseSerializer):
    data = NotificationSerializer()
