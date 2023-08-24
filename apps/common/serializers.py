from rest_framework import serializers


class SuccessResponseSerializer(serializers.Serializer):
    status = serializers.CharField(default="success")
    message = serializers.CharField()

class ErrorResponseSerializer(SuccessResponseSerializer):
    status = serializers.CharField(default="failure")

class ErrorDataResponseSerializer(ErrorResponseSerializer):
    data = serializers.DictField()