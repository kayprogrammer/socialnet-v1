from rest_framework import serializers


class SuccessResponseSerializer(serializers.Serializer):
    status = serializers.CharField(default="success")
    message = serializers.CharField()
