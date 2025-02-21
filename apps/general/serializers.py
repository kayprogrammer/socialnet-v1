from rest_framework import serializers
from apps.common.serializers import SuccessResponseSerializer


class SiteDetailSerializer(serializers.Serializer):
    name = serializers.CharField(default="SocialNet")
    email = serializers.EmailField(default="kayprogrammer1@gmail.com")
    phone = serializers.CharField(default="+2348133831036")
    address = serializers.CharField(default="234, Lagos, Nigeria")
    fb = serializers.CharField(default="https://facebook.com")
    tw = serializers.CharField(default="https://twitter.com")
    wh = serializers.CharField(default="https://wa.me/2348133831036")
    ig = serializers.CharField(default="https://instagram.com")


class SiteDetailResponseSerializer(SuccessResponseSerializer):
    data = SiteDetailSerializer()
