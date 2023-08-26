from adrf.views import APIView
from drf_spectacular.utils import extend_schema
from apps.common.responses import CustomResponse
from .models import Post

from .serializers import PostSerializer, PostsResponseSerializer
from asgiref.sync import sync_to_async

tags = ["Feed"]


class PostsView(APIView):
    serializer_class = PostSerializer

    @extend_schema(
        summary="Retrieve Latest Posts",
        description="This endpoint retrieves paginated responses of latest posts",
        tags=tags,
        responses=PostsResponseSerializer,
    )
    async def get(self, request):
        posts = await sync_to_async(list)(
            Post.objects.select_related("author", "image").prefetch_related("reactions")
        )
        serializer = self.serializer_class(posts, many=True)
        return CustomResponse.success(message="Posts fetched", data=serializer.data)
