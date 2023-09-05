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
    username = serializers.CharField()
    email = serializers.EmailField()
    avatar = serializers.CharField(source="get_avatar", default="https://img.url")
    bio = serializers.CharField(max_length=200)
    dob = serializers.DateField()
    city = serializers.CharField(source="city.name", allow_null=True)

    created_at = serializers.DateTimeField(default_timezone=pytz.timezone("UTC"))
    updated_at = serializers.DateTimeField(default_timezone=pytz.timezone("UTC"))

    class Meta:
        read_only_fields = ("created_at", "updated_at", "username", "avatar")


# RESPONSE SERIALIZERS
class ProfileResponseSerializer(SuccessResponseSerializer):
    data = ProfileSerializer
