import pytz
from rest_framework import serializers
from apps.common.serializers import SuccessResponseSerializer
from apps.common.file_processors import FileProcessor
from apps.common.validators import validate_image_type

def get_user(user):
    return {
        "name": user.full_name,
        "slug": user.username,
        "avatar": user.get_avatar,
    }


# POSTS


class ProfileSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=50)
    last_name = serializers.CharField(max_length=50)
    username = serializers.CharField(read_only=True)
    email = serializers.EmailField()
    avatar = serializers.SerializerMethodField(default="https://img.url")
    bio = serializers.CharField(max_length=200)
    dob = serializers.DateField()
    country = serializers.CharField(source="country.name")
    state = serializers.CharField(source="state.name")
    city = serializers.CharField(source="city.name")

    created_at = serializers.DateTimeField(
        default_timezone=pytz.timezone("UTC"), read_only=True
    )
    updated_at = serializers.DateTimeField(
        default_timezone=pytz.timezone("UTC"), read_only=True
    )

    def get_avatar(self, obj) -> str:
        return obj.get_avatar


# RESPONSE SERIALIZERS
class ProfileResponseSerializer(SuccessResponseSerializer):
    data = ProfileSerializer
