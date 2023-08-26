from rest_framework import serializers
from apps.common.serializers import SuccessResponseSerializer


class PostSerializer(serializers.Serializer):
    author = serializers.SerializerMethodField()
    text = serializers.CharField()
    slug = serializers.SlugField()
    reactions_count = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    def get_author(self, obj):
        author = obj.author
        return {
            "name": author.full_name,
            "slug": author.username,
            "avatar": author.get_avatar,
        }

    def get_reactions_count(self, obj):
        return obj.reactions.count()

    def get_image(self, obj):
        return obj.get_image


class PostsResponseSerializer(SuccessResponseSerializer):
    data = PostSerializer(many=True)
