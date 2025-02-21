import pytz
from rest_framework import serializers
from apps.common.serializers import (
    PaginatedResponseDataSerializer,
    SuccessResponseSerializer,
)
from apps.common.file_processors import FileProcessor
from apps.common.validators import validate_image_type
from apps.common.schema_examples import file_upload_data, user_data
from .models import REACTION_CHOICES


def get_user(user):
    return {
        "name": user.full_name,
        "username": user.username,
        "avatar": user.get_avatar,
    }


# POSTS

user_field = serializers.SerializerMethodField(default=user_data)


class PostSerializer(serializers.Serializer):
    author = user_field
    text = serializers.CharField()
    slug = serializers.SlugField(
        default="john-doe-d10dde64-a242-4ed0-bd75-4c759644b3a6", read_only=True
    )
    reactions_count = serializers.IntegerField(default=0, read_only=True)
    comments_count = serializers.IntegerField(default=0, read_only=True)

    image = serializers.CharField(
        source="get_image", default="https://img.url", read_only=True
    )
    file_type = serializers.CharField(
        write_only=True, required=False, validators=[validate_image_type]
    )
    created_at = serializers.DateTimeField(
        default_timezone=pytz.timezone("UTC"), read_only=True
    )
    updated_at = serializers.DateTimeField(
        default_timezone=pytz.timezone("UTC"), read_only=True
    )

    def get_author(self, obj) -> dict:
        return get_user(obj.author)


# RESPONSE SERIALIZERS
class PostCreateResponseDataSerializer(PostSerializer):
    file_upload_data = serializers.SerializerMethodField(default=file_upload_data)

    def get_fields(self, *args, **kwargs):
        fields = super().get_fields(*args, **kwargs)
        fields.pop("image", None)
        fields.pop("reactions_count", None)
        fields.pop("comments_count", None)
        return fields

    def get_file_upload_data(self, obj) -> dict:
        image_upload_status = self.context.get("image_upload_status")
        if image_upload_status:
            return FileProcessor.generate_file_signature(
                key=obj.image_id,
                folder="posts",
            )
        return None


class PostsResponseDataSerializer(PaginatedResponseDataSerializer):
    posts = PostSerializer(source="items", many=True)


class PostsResponseSerializer(SuccessResponseSerializer):
    data = PostsResponseDataSerializer()


class PostResponseSerializer(SuccessResponseSerializer):
    data = PostSerializer()


class PostCreateResponseSerializer(SuccessResponseSerializer):
    data = PostCreateResponseDataSerializer()


# REACTIONS


class ReactionSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    user = user_field
    rtype = serializers.ChoiceField(choices=REACTION_CHOICES, default="LIKE")

    def get_user(self, obj) -> dict:
        return get_user(obj.user)


class ReactionsResponseDataSerializer(PaginatedResponseDataSerializer):
    reactions = ReactionSerializer(source="items", many=True)


class ReactionsResponseSerializer(SuccessResponseSerializer):
    data = ReactionsResponseDataSerializer()


# COMMENTS & REPLIES
class ReplySerializer(serializers.Serializer):
    author = user_field
    slug = serializers.CharField(read_only=True)
    text = serializers.CharField()
    reactions_count = serializers.IntegerField(default=0, read_only=True)

    def get_author(self, obj) -> dict:
        return get_user(obj.author)


class CommentSerializer(ReplySerializer):
    replies_count = serializers.IntegerField(default=0, read_only=True)


class CommentWithRepliesResponseDataSerializer(PaginatedResponseDataSerializer):
    items = ReplySerializer(many=True)


class CommentWithRepliesSerializer(serializers.Serializer):
    comment = CommentSerializer()
    replies = CommentWithRepliesResponseDataSerializer()


class CommentsResponseDataSerializer(PaginatedResponseDataSerializer):
    comments = CommentSerializer(source="items", many=True)


class CommentsResponseSerializer(SuccessResponseSerializer):
    data = CommentsResponseDataSerializer(many=True)


class CommentResponseSerializer(SuccessResponseSerializer):
    data = CommentSerializer()


class CommentWithRepliesResponseSerializer(SuccessResponseSerializer):
    data = CommentWithRepliesSerializer()


class ReplyResponseSerializer(SuccessResponseSerializer):
    data = ReplySerializer()
