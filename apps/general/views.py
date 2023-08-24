from adrf.views import APIView
from drf_spectacular.utils import extend_schema
from apps.common.responses import CustomResponse

from apps.general.models import SiteDetail
from apps.general.serializers import SiteDetailSerializer, SiteDetailResponseSerializer


class SiteDetailView(APIView):
    serializer_class = SiteDetailSerializer

    @extend_schema(
        summary="Retrieve site details",
        description="This endpoint retrieves few details of the site/application",
        responses=SiteDetailResponseSerializer,
    )
    async def get(self, request):
        sitedetail, created = await SiteDetail.objects.aget_or_create()
        serializer = self.serializer_class(sitedetail)
        return CustomResponse.success(
            message="Site Details fetched", data=serializer.data
        )
