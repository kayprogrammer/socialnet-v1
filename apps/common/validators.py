from rest_framework import serializers
from apps.common.file_types import ALLOWED_IMAGE_TYPES


def validate_image_type(value):
    if value and value not in ALLOWED_IMAGE_TYPES:
        raise serializers.ValidationError("Image type not allowed!")
    return value
