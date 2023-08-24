from rest_framework import serializers
from apps.common.serializers import SuccessResponseSerializer


class SiteDetailSerializer(serializers.Serializer):
    name = serializers.CharField()
    email = serializers.EmailField()
    phone = serializers.CharField()
    address = serializers.CharField()
    fb = serializers.CharField()
    tw = serializers.CharField()
    wh = serializers.CharField()
    ig = serializers.CharField()


class SiteDetailResponseSerializer(SuccessResponseSerializer):
    data = SiteDetailSerializer()
