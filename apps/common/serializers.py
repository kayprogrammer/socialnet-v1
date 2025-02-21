from rest_framework import serializers


class SuccessResponseSerializer(serializers.Serializer):
    status = serializers.CharField(default="success")
    message = serializers.CharField()


class ErrorResponseSerializer(SuccessResponseSerializer):
    status = serializers.CharField(default="failure")


class ErrorDataResponseSerializer(ErrorResponseSerializer):
    data = serializers.DictField()


class PaginatedResponseDataSerializer(serializers.Serializer):
    per_page = serializers.IntegerField()
    current_page = serializers.IntegerField()
    last_page = serializers.IntegerField()
