from django.contrib import admin
from django.utils.safestring import mark_safe
from cities_light.models import SubRegion

admin.site.site_header = mark_safe(
    '<strong style="font-weight:bold;">SOCIALNET V1 ADMIN</strong>'
)

admin.site.unregister(SubRegion)
