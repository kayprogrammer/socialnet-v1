from adrf.views import APIView
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema, OpenApiParameter
from asgiref.sync import sync_to_async

from .models import Post
from .serializers import (
    PostSerializer,
    PostsResponseSerializer,
    PostResponseSerializer,
    PostCreateResponseSerializer,
    PostCreateResponseDataSerializer,
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


class PostsView(APIView):
    serializer_class = PostSerializer
    post_resp_serializer_class = PostCreateResponseDataSerializer
    paginator_class = PageNumberPagination()

    @extend_schema(
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
            Post.objects.select_related("author", "image").prefetch_related("reactions")
        )
        paginated_posts = self.paginator_class.paginate_queryset(posts, request)
        serializer = self.serializer_class(paginated_posts, many=True)
        return CustomResponse.success(message="Posts fetched", data=serializer.data)

    @extend_schema(
        summary="Create Post",
        description="This endpoint creates a new post",
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
        return CustomResponse.success(
            message="Post updated", data=serializer.data, status_code=200
        )

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
