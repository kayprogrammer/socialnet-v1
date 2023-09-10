from django.contrib import admin

from apps.profiles.models import Friend


class FriendAdmin(admin.ModelAdmin):
    list_display = ("requester", "requestee", "status", "created_at", "updated_at")
    list_filter = ("requester", "requestee", "status", "created_at", "updated_at")


admin.site.register(Friend, FriendAdmin)
