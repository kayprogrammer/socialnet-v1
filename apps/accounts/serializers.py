from email.policy import default
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from apps.common.serializers import SuccessResponseSerializer


# REQUEST SERIALIZERS
class RegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField(
        max_length=50, error_messages={"max_length": _("{max_length} characters max.")}
    )
    last_name = serializers.CharField(
        max_length=50, error_messages={"max_length": _("{max_length} characters max.")}
    )
    email = serializers.EmailField()
    password = serializers.CharField(
        min_length=8, error_messages={"min_length": _("{min_length} characters min.")}
    )
    terms_agreement = serializers.BooleanField()

    def validate(self, attrs):
        first_name = attrs["first_name"]
        last_name = attrs["last_name"]
        terms_agreement = attrs["terms_agreement"]

        if len(first_name.split(" ")) > 1:
            raise serializers.ValidationError({"first_name": "No spacing allowed"})

        if len(last_name.split(" ")) > 1:
            raise serializers.ValidationError({"last_name": "No spacing allowed"})

        if terms_agreement != True:
            raise serializers.ValidationError(
                {"terms_agreement": "You must agree to terms and conditions"}
            )
        return attrs


class ResendOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()


class VerifyOtpSerializer(ResendOtpSerializer):
    otp = serializers.IntegerField()


class SetNewPasswordSerializer(VerifyOtpSerializer):
    password = serializers.CharField(
        min_length=8, error_messages={"min_length": _("{min_length} characters min.")}
    )


class LoginSerializer(ResendOtpSerializer):
    password = serializers.CharField()


class RefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()


# RESPONSE SERIALIZERS
class RegisterResponseSerializer(SuccessResponseSerializer):
    data = serializers.DictField(default={"email": "johndoe@example.com"})


class LoginResponseSerializer(SuccessResponseSerializer):
    data = serializers.DictField(
        default={
            "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.",
            "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6InVzZXJuYW1lMSIsInBhc3N3b3JkIjoiYXNkZmFzZGYiLCJpYXQiOjE2MzA2MzA3NTh9.",
        }
    )
