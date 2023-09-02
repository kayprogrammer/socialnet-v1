import pytz
from rest_framework import serializers
from apps.common.serializers import SuccessResponseSerializer
from apps.common.file_processors import FileProcessor
from apps.common.validators import validate_image_type
from .models import REACTION_CHOICES


def get_user(user):
    return {
        "name": user.full_name,
        "slug": user.username,
        "avatar": user.get_avatar,
    }


# POSTS

user_field = serializers.SerializerMethodField(
    default={"name": "John Doe", "slug": "john-doe", "avatar": "https://img.url"}
)


class PostSerializer(serializers.Serializer):
    author = user_field
    text = serializers.CharField()
    slug = serializers.SlugField(
        default="john-doe-d10dde64-a242-4ed0-bd75-4c759644b3a6", read_only=True
    )
    reactions_count = serializers.IntegerField(default=0, read_only=True)
    comments_count = serializers.IntegerField(default=0, read_only=True)

    image = serializers.SerializerMethodField(default="https://img.url")
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

    def get_image(self, obj) -> str:
        return obj.get_image


# RESPONSE SERIALIZERS
class PostCreateResponseDataSerializer(PostSerializer):
    file_upload_data = serializers.SerializerMethodField(
        default={
            "public_id": "d23dde64-a242-4ed0-bd75-4c759624b3a6",
            "signature": "djsdsjAushsh",
            "timestamp": "16272637829",
        }
    )

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


class PostsResponseSerializer(SuccessResponseSerializer):
    data = PostSerializer(many=True)


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


class ReactionsResponseSerializer(SuccessResponseSerializer):
    data = ReactionSerializer(many=True)


# COMMENTS & REPLIES
class ReplySerializer(serializers.Serializer):
    author = user_field
    slug = serializers.CharField(read_only=True)
    text = serializers.CharField()

    def get_author(self, obj) -> dict:
        return get_user(obj.author)


class CommentSerializer(ReplySerializer):
    replies_count = serializers.IntegerField(default=0, read_only=True)


class CommentWithRepliesSerializer(serializers.Serializer):
    comment = CommentSerializer()
    replies = ReplySerializer(many=True)


class CommentsResponseSerializer(SuccessResponseSerializer):
    data = CommentSerializer(many=True)


class CommentResponseSerializer(SuccessResponseSerializer):
    data = CommentSerializer()


class CommentWithRepliesResponseSerializer(SuccessResponseSerializer):
    data = CommentWithRepliesSerializer()
