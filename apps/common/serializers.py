from rest_framework import serializers

class SuccessResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    message = serializers.CharField()
    data = serializers.DictField()

    def get_fields(self):
        print(vars(self.context))
        print("Haa")
        return super().get_fields()