from django.db.models import Count
from adrf.views import APIView
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema, OpenApiParameter
from asgiref.sync import sync_to_async

from apps.common.file_types import ALLOWED_IMAGE_TYPES

from .models import Post, Comment, Reply, Reaction, REACTION_CHOICES
from .serializers import (
    CommentSerializer,
    CommentsResponseSerializer,
    PostSerializer,
    PostsResponseSerializer,
    PostResponseSerializer,
    PostCreateResponseSerializer,
    PostCreateResponseDataSerializer,
    ReactionSerializer,
    ReactionsResponseSerializer,
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
    paginator_class = PageNumberPagination()

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
            Post.objects.select_related("author", "image")
            .annotate(
                reactions_count=Count("reactions"), comments_count=Count("comments")
            )
            .order_by("-created_at")
        )
        paginated_posts = self.paginator_class.paginate_queryset(posts, request)
        serializer = self.serializer_class(paginated_posts, many=True)
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
        file_type = data.get("file_type")
        image_upload_status = False
        if file_type:
            file = await File.objects.acreate(resource_type=file_type)
            data["image_id"] = file.id
            data.pop("file_type")
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
            await Post.objects.select_related("author", "image")
            .prefetch_related("reactions")
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
        post = await self.get_object(kwargs.get("slug"))
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
        post = await self.get_object(kwargs.get("slug"))
        if post.author != request.user:
            raise RequestError(
                err_code=ErrorCode.INVALID_OWNER,
                err_msg="This Post isn't yours",
            )
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        file_type = data.get("file_type")
        image_upload_status = False
        if file_type:
            file = post.image
            if not file:
                file = await File.objects.acreate(resource_type=file_type)
            else:
                file.resource_type = file_type
                await file.asave()
            data["image_id"] = file.id
            data.pop("file_type")
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
        post = await self.get_object(kwargs.get("slug"))
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
        name="for",
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
    paginator_class = PageNumberPagination()
    reaction_for = {"POST": Post, "COMMENT": Comment, "REPLY": Reply}
    params = reactions_params
    get_params = params + [
        OpenApiParameter(
            name="type",
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

    def validate_for(self, value):
        if not value in list(self.reaction_for.keys()):
            raise RequestError(
                err_code=ErrorCode.INVALID_VALUE,
                err_msg="Invalid 'for' value",
                status_code=404,
            )
        return value

    async def get_object(self, value, slug):
        value = self.validate_for(value)
        model = self.reaction_for[value]
        obj = await model.objects.aget_or_none(slug=slug)
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
            Reaction.objects.filter(**filter).select_related("user")
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
        rtype = request.GET.get("type")
        if rtype and rtype not in set(item[0] for item in REACTION_CHOICES):
            raise RequestError(
                err_code=ErrorCode.INVALID_VALUE,
                err_msg="Invalid reaction type",
                status_code=404,
            )
        reactions = await self.get_queryset(
            kwargs.get("for"), kwargs.get("slug"), rtype
        )
        paginated_reactions = self.paginator_class.paginate_queryset(reactions, request)
        serializer = self.serializer_class(paginated_reactions, many=True)
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
        for_val = kwargs.get("for")
        obj = await self.get_object(for_val, kwargs.get("slug"))
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        data["user"] = request.user
        rtype = data.pop("rtype")
        data[f"{for_val.lower()}_id"] = obj.id
        reaction, created = await Reaction.objects.select_related(
            "user"
        ).aupdate_or_create(**data, defaults={"rtype": rtype})
        serializer = self.serializer_class(reaction)
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
        reaction = await Reaction.objects.aget_or_none(id=kwargs.get("id"))
        if not reaction:
            raise RequestError(
                err_code=ErrorCode.NON_EXISTENT,
                err_msg="Reaction does not exist",
                status_code=404,
            )
        if request.user.id != reaction.user_id:
            raise RequestError(
                err_code=ErrorCode.INVALID_OWNER,
                err_msg="Not yours to delete",
                status_code=401,
            )
        await reaction.adelete()
        return CustomResponse.success(message="Reaction deleted")


# COMMENTS
class CommentsView(APIView):
    serializer_class = CommentSerializer
    paginator_class = PageNumberPagination()

    @extend_schema(
        summary="Retrieve Post Comments",
        description="""
            This endpoint retrieves comments of a particular post.
        """,
        tags=tags,
        responses=CommentsResponseSerializer,
    )
    async def get(self, request, *args, **kwargs):
        post = await Post.objects.aget_or_none(slug=kwargs.get("slug"))
        if not post:
            raise RequestError(
                err_code=ErrorCode.NON_EXISTENT,
                err_msg="Post does not exist",
                status_code=404,
            )
        comments = await sync_to_async(list)(
            Comment.objects.filter(post_id=post.id)
            .select_related("author")
            .annotate(replies_count=Count("replies"))
        )
        paginated_comments = self.paginator_class.paginate_queryset(comments, request)
        serializer = self.serializer_class(paginated_comments, many=True)
        return CustomResponse.success(message="Comments Fetched", data=serializer.data)
