from django.db.models import Count
from adrf.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter
from asgiref.sync import sync_to_async

from apps.common.file_types import ALLOWED_IMAGE_TYPES
from apps.common.paginators import CustomPagination
from apps.profiles.models import Notification
from apps.profiles.utils import send_notification_in_socket

from .models import Post, Comment, Reply, Reaction, REACTION_CHOICES
from .serializers import (
    CommentResponseSerializer,
    CommentSerializer,
    CommentWithRepliesResponseSerializer,
    CommentWithRepliesSerializer,
    CommentsResponseDataSerializer,
    CommentsResponseSerializer,
    PostSerializer,
    PostsResponseDataSerializer,
    PostsResponseSerializer,
    PostResponseSerializer,
    PostCreateResponseSerializer,
    PostCreateResponseDataSerializer,
    ReactionSerializer,
    ReactionsResponseDataSerializer,
    ReactionsResponseSerializer,
    ReplyResponseSerializer,
    ReplySerializer,
)

from apps.common.models import File
from apps.common.error import ErrorCode
from apps.common.exceptions import RequestError
from apps.common.serializers import ErrorResponseSerializer, SuccessResponseSerializer
from apps.common.responses import CustomResponse
from apps.common.utils import (
    IsAuthenticatedCustom,
)

tags = ["Feed"]

# POSTS


class PostsView(APIView):
    serializer_class = PostSerializer
    post_resp_serializer_class = PostCreateResponseDataSerializer
    paginator_class = CustomPagination()

    @extend_schema(
        operation_id="posts_list",
        summary="Retrieve Latest Posts",
        description="This endpoint retrieves paginated responses of latest posts",
        tags=tags,
        responses=PostsResponseSerializer,
        parameters=[
            OpenApiParameter(
                name="page",
                description="Retrieve a particular page of posts. Defaults to 1",
                required=False,
                type=int,
            )
        ],
    )
    async def get(self, request):
        posts = await sync_to_async(list)(
            Post.objects.select_related("author", "author__avatar", "image")
            .annotate(
                reactions_count=Count("reactions"), comments_count=Count("comments")
            )
            .order_by("-created_at")
        )
        paginated_data = self.paginator_class.paginate_queryset(posts, request)
        serializer = PostsResponseDataSerializer(paginated_data)
        return CustomResponse.success(message="Posts fetched", data=serializer.data)

    @extend_schema(
        operation_id="posts_create",
        summary="Create Post",
        description=f"""
            This endpoint creates a new post
            ALLOWED FILE TYPES: {", ".join(ALLOWED_IMAGE_TYPES)}
        """,
        tags=tags,
        responses={201: PostCreateResponseSerializer},
    )
    async def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        file_type = data.pop("file_type", None)
        image_upload_status = False
        if file_type:
            file = await File.objects.acreate(resource_type=file_type)
            data["image_id"] = file.id
            image_upload_status = True

        data["author"] = request.user
        post = await Post.objects.acreate(**data)
        serializer = self.post_resp_serializer_class(
            post, context={"image_upload_status": image_upload_status}
        )
        return CustomResponse.success(
            message="Post created", data=serializer.data, status_code=201
        )

    def get_permissions(self):
        permissions = []
        if self.request.method == "POST":
            permissions = [
                IsAuthenticatedCustom(),
            ]
        return permissions


class PostDetailView(APIView):
    serializer_class = PostSerializer
    put_resp_serializer_class = PostCreateResponseDataSerializer

    async def get_object(self, slug):
        post = (
            await Post.objects.select_related("author", "author__avatar", "image")
            .annotate(
                reactions_count=Count("reactions"), comments_count=Count("comments")
            )
            .aget_or_none(slug=slug)
        )
        if not post:
            raise RequestError(
                err_code=ErrorCode.NON_EXISTENT,
                err_msg="No post with that slug",
                status_code=404,
            )
        return post

    @extend_schema(
        summary="Retrieve Single Post",
        description="This endpoint retrieves a single post",
        tags=tags,
        responses={200: PostResponseSerializer, 404: ErrorResponseSerializer},
    )
    async def get(self, request, *args, **kwargs):
        post = await self.get_object(kwargs["slug"])
        serializer = self.serializer_class(post)
        return CustomResponse.success(
            message="Post Detail fetched", data=serializer.data
        )

    @extend_schema(
        summary="Update a Post",
        description="This endpoint updates a post",
        tags=tags,
        responses={200: PostCreateResponseSerializer},
    )
    async def put(self, request, *args, **kwargs):
        post = await self.get_object(kwargs["slug"])
        if post.author != request.user:
            raise RequestError(
                err_code=ErrorCode.INVALID_OWNER,
                err_msg="This Post isn't yours",
            )
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        file_type = data.pop("file_type", None)
        image_upload_status = False
        if file_type:
            file = post.image
            if not file:
                file = await File.objects.acreate(resource_type=file_type)
            else:
                file.resource_type = file_type
                await file.asave()
            data["image_id"] = file.id
            image_upload_status = True

        for attr, value in data.items():
            setattr(post, attr, value)
        await post.asave()

        serializer = self.put_resp_serializer_class(
            post, context={"image_upload_status": image_upload_status}
        )
        return CustomResponse.success(message="Post updated", data=serializer.data)

    @extend_schema(
        summary="Delete a Post",
        description="This endpoint deletes a post",
        tags=tags,
        responses={200: SuccessResponseSerializer},
    )
    async def delete(self, request, *args, **kwargs):
        post = await self.get_object(kwargs["slug"])
        if post.author != request.user:
            raise RequestError(
                err_code=ErrorCode.INVALID_OWNER,
                err_msg="This Post isn't yours",
            )
        await post.adelete()
        return CustomResponse.success(message="Post deleted")

    def get_permissions(self):
        permissions = []
        if self.request.method != "GET":
            permissions = [
                IsAuthenticatedCustom(),
            ]
        return permissions


# REACTIONS
reactions_params = [
    OpenApiParameter(
        name="focus",
        description="""
            Specify the usage. Use any of the three: POST, COMMENT, FEED
        """,
        required=True,
        type=str,
        location="path",
    ),
    OpenApiParameter(
        name="slug",
        description="Enter the slug of the post or comment or reply",
        required=True,
        type=str,
        location="path",
    ),
]


class ReactionsView(APIView):
    serializer_class = ReactionSerializer
    paginator_class = CustomPagination()
    reaction_focus = {"POST": Post, "COMMENT": Comment, "REPLY": Reply}
    params = reactions_params
    get_params = params + [
        OpenApiParameter(
            name="reaction_type",
            description="""
                Retrieve a particular type of reactions. Use any of the six (all uppercase):
                LIKE, LOVE, HAHA, WOW, SAD, ANGRY
            """,
            required=False,
            type=str,
        ),
        OpenApiParameter(
            name="page",
            description="""
                Retrieve a particular page of reactions. Defaults to 1
            """,
            required=False,
            type=int,
        ),
    ]

    def validate_focus(self, value):
        if not value in list(self.reaction_focus.keys()):
            raise RequestError(
                err_code=ErrorCode.INVALID_VALUE,
                err_msg="Invalid 'focus' value",
                status_code=404,
            )
        return value

    async def get_object(self, value, slug):
        value = self.validate_focus(value)
        model = self.reaction_focus[value]
        related = ["author"]
        if model == Comment:
            related.append("post")
        obj = await model.objects.select_related(*related).aget_or_none(slug=slug)
        if not obj:
            raise RequestError(
                err_code=ErrorCode.NON_EXISTENT,
                err_msg=f"{value.capitalize()} does not exist",
                status_code=404,
            )
        return obj

    async def get_queryset(self, value, slug, rtype=None):
        obj = await self.get_object(value, slug)
        field_name = f"{value.lower()}_id"
        filter = {field_name: obj.id}
        if rtype:
            filter["rtype"] = rtype
        reactions = await sync_to_async(list)(
            Reaction.objects.filter(**filter).select_related("user", "avatar")
        )
        return reactions

    @extend_schema(
        summary="Retrieve Latest Reactions of a Post, Comment, or Reply",
        description="""
            This endpoint retrieves paginated responses of reactions of post, comment, reply.
        """,
        tags=tags,
        responses=ReactionsResponseSerializer,
        parameters=get_params,
    )
    async def get(self, request, *args, **kwargs):
        rtype = request.GET.get("reaction_type")
        if rtype and rtype not in set(item[0] for item in REACTION_CHOICES):
            raise RequestError(
                err_code=ErrorCode.INVALID_VALUE,
                err_msg="Invalid reaction type",
                status_code=404,
            )
        reactions = await self.get_queryset(kwargs["focus"], kwargs["slug"], rtype)
        paginated_data = self.paginator_class.paginate_queryset(reactions, request)
        serializer = ReactionsResponseDataSerializer(paginated_data)
        return CustomResponse.success(message="Reactions fetched", data=serializer.data)

    @extend_schema(
        summary="Create Reaction",
        description="""
            This endpoint creates a new reaction
            rtype should be any of these:
            
            - LIKE    - LOVE
            - HAHA    - WOW
            - SAD     - ANGRY
        """,
        tags=tags,
        responses=ReactionsResponseSerializer,
        parameters=params,
    )
    async def post(self, request, *args, **kwargs):
        user = request.user
        for_val = kwargs["for"]
        obj = await self.get_object(for_val, kwargs["slug"])
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        data["user"] = user
        rtype = data.pop("rtype")
        obj_field = for_val.lower()
        data[obj_field] = obj

        reaction = await Reaction.objects.select_related(
            "user", "user__avatar"
        ).aget_or_none(**data)
        if reaction:
            reaction.rtype = rtype
            await reaction.asave()
        else:
            data["rtype"] = rtype
            reaction = await Reaction.objects.acreate(**data)

        serializer = self.serializer_class(reaction)

        # Create and Send Notification
        if obj.author_id != user.id:
            ndata = {obj_field: obj}
            notification, created = await Notification.objects.select_related(
                "sender",
                "sender__avatar",
                "post",
                "comment",
                "comment__post",
                "reply",
                "reply__comment",
                "reply__comment__post",
            ).aget_or_create(sender=user, ntype="REACTION", **ndata)
            if created:
                await notification.receivers.aadd(obj.author)

                # Send to websocket
                await send_notification_in_socket(
                    request.is_secure(),
                    request.get_host(),
                    notification,
                )

        return CustomResponse.success(
            message="Reaction created", data=serializer.data, status_code=201
        )

    def get_permissions(self):
        permissions = []
        if self.request.method == "POST":
            permissions = [
                IsAuthenticatedCustom(),
            ]
        return permissions


class RemoveReaction(APIView):
    permission_classes = (IsAuthenticatedCustom,)

    @extend_schema(
        summary="Remove Reaction",
        description="""
            This endpoint deletes a reaction.
        """,
        tags=tags,
        responses={200: SuccessResponseSerializer},
    )
    async def delete(self, request, *args, **kwargs):
        user = request.user
        reaction = await Reaction.objects.select_related(
            "post", "comment", "reply"
        ).aget_or_none(id=kwargs["id"])
        if not reaction:
            raise RequestError(
                err_code=ErrorCode.NON_EXISTENT,
                err_msg="Reaction does not exist",
                status_code=404,
            )
        if user.id != reaction.user_id:
            raise RequestError(
                err_code=ErrorCode.INVALID_OWNER,
                err_msg="Not yours to delete",
                status_code=401,
            )

        # Remove Reaction Notification
        targeted_obj = reaction.targeted_obj
        targeted_field = f"{targeted_obj.__class__.__name__.lower()}_id"  # (post_id, comment_id or reply_id)
        data = {
            "sender": user,
            "ntype": "REACTION",
            targeted_field: targeted_obj.id,
        }

        notification = await Notification.objects.aget_or_none(**data)
        if notification:
            # Send to websocket and delete notification
            await send_notification_in_socket(
                request.is_secure(), request.get_host(), notification, status="DELETED"
            )
            await notification.adelete()

        await reaction.adelete()
        return CustomResponse.success(message="Reaction deleted")


# COMMENTS
class CommentsView(APIView):
    serializer_class = CommentSerializer
    paginator_class = CustomPagination()

    async def get_object(self, slug):
        post = await Post.objects.select_related(
            "author", "author__avatar"
        ).aget_or_none(slug=slug)
        if not post:
            raise RequestError(
                err_code=ErrorCode.NON_EXISTENT,
                err_msg="Post does not exist",
                status_code=404,
            )
        return post

    @extend_schema(
        summary="Retrieve Post Comments",
        description="""
            This endpoint retrieves comments of a particular post.
        """,
        tags=tags,
        responses=CommentsResponseSerializer,
        parameters=[
            OpenApiParameter(
                name="page",
                description="""
                Retrieve a particular page of comments. Defaults to 1
            """,
                required=False,
                type=int,
            ),
        ],
    )
    async def get(self, request, *args, **kwargs):
        post = await self.get_object(kwargs["slug"])
        comments = await sync_to_async(list)(
            Comment.objects.filter(post_id=post.id)
            .select_related("author", "author__avatar")
            .annotate(replies_count=Count("replies"))
        )
        paginated_data = self.paginator_class.paginate_queryset(comments, request)
        serializer = CommentsResponseDataSerializer(paginated_data)

        return CustomResponse.success(message="Comments Fetched", data=serializer.data)

    @extend_schema(
        summary="Create Comment",
        description="""
            This endpoint creates a comment for a particular post.
        """,
        tags=tags,
        responses={201: CommentResponseSerializer},
    )
    async def post(self, request, *args, **kwargs):
        user = request.user
        post = await self.get_object(kwargs["slug"])
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        data.update({"post": post, "author": user})

        comment = await Comment.objects.acreate(**data)
        serializer = self.serializer_class(comment)

        # Create and Send Notification
        if user.id != post.author_id:
            notification = await Notification.objects.acreate(
                sender=user, ntype="COMMENT", comment=comment
            )
            await notification.receivers.aadd(post.author)

            # Send to websocket
            await send_notification_in_socket(
                request.is_secure(),
                request.get_host(),
                notification,
            )

        return CustomResponse.success(
            message="Comment Created", data=serializer.data, status_code=201
        )

    def get_permissions(self):
        permissions = []
        if self.request.method == "POST":
            permissions = [
                IsAuthenticatedCustom(),
            ]
        return permissions


class CommentView(APIView):
    serializer_class = CommentWithRepliesSerializer
    paginator_class = CustomPagination()
    common_param = [
        OpenApiParameter(
            name="slug",
            description="""
                Enter the slug of the comment
            """,
            required=True,
            type=str,
            location="path",
        ),
    ]

    async def get_object(self, slug):
        comment = (
            await Comment.objects.select_related("author", "author__avatar", "post")
            .annotate(replies_count=Count("replies"))
            .aget_or_none(slug=slug)
        )
        if not comment:
            raise RequestError(
                err_code=ErrorCode.NON_EXISTENT,
                err_msg="Comment does not exist",
                status_code=404,
            )
        return comment

    @extend_schema(
        summary="Retrieve Comment with replies",
        description="""
            This endpoint retrieves a comment with replies.
        """,
        tags=tags,
        responses=CommentWithRepliesResponseSerializer,
        parameters=common_param
        + [
            OpenApiParameter(
                name="page",
                description="""
                Retrieve a particular page of replies. Defaults to 1
            """,
                required=False,
                type=int,
            ),
        ],
    )
    async def get(self, request, *args, **kwargs):
        comment = await self.get_object(kwargs["slug"])
        replies = await sync_to_async(list)(
            Reply.objects.filter(comment_id=comment.id).select_related(
                "author", "author__avatar"
            )
        )
        paginated_data = self.paginator_class.paginate_queryset(replies, request)
        data = {"comment": comment, "replies": paginated_data}
        serializer = self.serializer_class(data)
        return CustomResponse.success(
            message="Comment and Replies Fetched", data=serializer.data
        )

    @extend_schema(
        summary="Create Reply",
        description="""
            This endpoint creates a reply for a comment.
        """,
        tags=tags,
        request=ReplySerializer,
        responses=ReplySerializer,
        parameters=common_param,
    )
    async def post(self, request, *args, **kwargs):
        user = request.user
        comment = await self.get_object(kwargs["slug"])
        serializer = ReplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        data["author"] = request.user
        data["comment"] = comment

        reply = await Reply.objects.acreate(**data)
        serializer = ReplySerializer(reply)

        # Create and Send Notification
        if user.id != comment.author_id:
            notification = await Notification.objects.acreate(
                sender=user, ntype="REPLY", reply=reply
            )
            await notification.receivers.aadd(comment.author)

            # Send to websocket
            await send_notification_in_socket(
                request.is_secure(),
                request.get_host(),
                notification,
            )

        return CustomResponse.success(
            message="Reply Created", data=serializer.data, status_code=201
        )

    @extend_schema(
        summary="Update Comment",
        description="""
            This endpoint updates a particular comment.
        """,
        parameters=common_param,
        tags=tags,
        request=CommentSerializer,
        responses=CommentResponseSerializer,
    )
    async def put(self, request, *args, **kwargs):
        comment = await self.get_object(kwargs["slug"])
        if comment.author_id != request.user.id:
            raise RequestError(
                err_code=ErrorCode.INVALID_OWNER,
                err_msg="Not yours to edit",
                status_code=401,
            )
        serializer = CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment.text = serializer.validated_data["text"]
        await comment.asave()
        serializer = CommentSerializer(comment)
        return CustomResponse.success(message="Comment Updated", data=serializer.data)

    @extend_schema(
        summary="Delete Comment",
        description="""
            This endpoint deletes a comment.
        """,
        parameters=common_param,
        tags=tags,
        responses={200: SuccessResponseSerializer},
    )
    async def delete(self, request, *args, **kwargs):
        user = request.user
        comment = await self.get_object(kwargs["slug"])
        if request.user.id != comment.author_id:
            raise RequestError(
                err_code=ErrorCode.INVALID_OWNER,
                err_msg="Not yours to delete",
                status_code=401,
            )

        # Remove Comment Notification
        notification = await Notification.objects.aget_or_none(
            sender=user, ntype="COMMENT", comment_id=comment.id
        )
        if notification:
            # Send to websocket and delete notification
            await send_notification_in_socket(
                request.is_secure(), request.get_host(), notification, status="DELETED"
            )
            await notification.adelete()

        await comment.adelete()
        return CustomResponse.success(message="Comment Deleted")

    def get_permissions(self):
        permissions = []
        if self.request.method != "GET":
            permissions = [
                IsAuthenticatedCustom(),
            ]
        return permissions


class ReplyView(APIView):
    serializer_class = ReplySerializer
    common_param = [
        OpenApiParameter(
            name="slug",
            description="""
                Enter the slug of the reply
            """,
            required=True,
            type=str,
            location="path",
        ),
    ]

    async def get_object(self, slug):
        reply = await Reply.objects.select_related(
            "author", "author__avatar"
        ).aget_or_none(slug=slug)
        if not reply:
            raise RequestError(
                err_code=ErrorCode.NON_EXISTENT,
                err_msg="Reply does not exist",
                status_code=404,
            )
        return reply

    @extend_schema(
        summary="Retrieve Reply",
        description="""
            This endpoint retrieves a reply.
        """,
        tags=tags,
        responses=ReplyResponseSerializer,
        parameters=common_param,
    )
    async def get(self, request, *args, **kwargs):
        reply = await self.get_object(kwargs["slug"])
        serializer = self.serializer_class(reply)
        return CustomResponse.success(message="Reply Fetched", data=serializer.data)

    @extend_schema(
        summary="Update Reply",
        description="""
            This endpoint updates a particular reply.
        """,
        parameters=common_param,
        tags=tags,
        responses=ReplyResponseSerializer,
    )
    async def put(self, request, *args, **kwargs):
        reply = await self.get_object(kwargs["slug"])
        if reply.author_id != request.user.id:
            raise RequestError(
                err_code=ErrorCode.INVALID_OWNER,
                err_msg="Not yours to edit",
                status_code=401,
            )
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        reply.text = serializer.validated_data["text"]
        await reply.asave()
        serializer = self.serializer_class(reply)
        return CustomResponse.success(message="Reply Updated", data=serializer.data)

    @extend_schema(
        summary="Delete reply",
        description="""
            This endpoint deletes a reply.
        """,
        parameters=common_param,
        tags=tags,
        responses={200: SuccessResponseSerializer},
    )
    async def delete(self, request, *args, **kwargs):
        user = request.user
        reply = await self.get_object(kwargs["slug"])
        if request.user.id != reply.author_id:
            raise RequestError(
                err_code=ErrorCode.INVALID_OWNER,
                err_msg="Not yours to delete",
                status_code=401,
            )

        # Remove Reply Notification
        notification = await Notification.objects.aget_or_none(
            sender=user, ntype="REPLY", reply_id=reply.id
        )
        if notification:
            # Send to websocket and delete notification
            await send_notification_in_socket(
                request.is_secure(), request.get_host(), notification, status="DELETED"
            )
            await notification.adelete()

        await reply.adelete()
        return CustomResponse.success(message="Reply Deleted")

    def get_permissions(self):
        permissions = []
        if self.request.method != "GET":
            permissions = [
                IsAuthenticatedCustom(),
            ]
        return permissions
