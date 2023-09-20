from rest_framework import serializers
from apps.common.file_types import ALLOWED_FILE_TYPES, ALLOWED_IMAGE_TYPES


def validate_image_type(value):
    if value and value not in ALLOWED_IMAGE_TYPES:
        raise serializers.ValidationError("Image type not allowed!")
    return value


def validate_file_type(value):
    if value and value not in ALLOWED_FILE_TYPES:
        raise serializers.ValidationError("File type not allowed!")
    return value
