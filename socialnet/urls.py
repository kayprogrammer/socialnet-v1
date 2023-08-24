from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from django.conf.urls.static import static
from django.conf import settings
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from drf_spectacular.utils import extend_schema
from adrf.views import APIView

from apps.common.responses import CustomResponse
from apps.common.serializers import SuccessResponseSerializer
import debug_toolbar


class HealthCheckView(APIView):
    @extend_schema(
        "/",
        summary="API Health Check",
        description="This endpoint checks the health of the API",
        responses=SuccessResponseSerializer,
    )
    async def get(self, request):
        return CustomResponse.success(message="pong")


def handler404(request, exception=None):
    response = JsonResponse({"status": "failure", "message": "Not Found"})
    response.status_code = 404
    return response


def handler500(request, exception=None):
    response = JsonResponse({"status": "failure", "message": "Server Error"})
    response.status_code = 500
    return response


handler404 = handler404
handler500 = handler500

urlpatterns = [
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("admin/", admin.site.urls),
    path("api/v1/general/", include("apps.general.urls")),
    path("api/v1/healthcheck/", HealthCheckView.as_view()),
    path("__debug__/", include(debug_toolbar.urls)),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
