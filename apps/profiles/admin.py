from django.contrib import admin

from apps.profiles.models import Friend, Notification


class FriendAdmin(admin.ModelAdmin):
    list_display = ("requester", "requestee", "status", "created_at", "updated_at")
    list_filter = ("requester", "requestee", "status", "created_at", "updated_at")


class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "sender", "ntype", "created_at", "updated_at")
    list_filter = (
        "sender",
        "receivers",
        "ntype",
        "read_by",
        "created_at",
        "updated_at",
    )


admin.site.register(Friend, FriendAdmin)
admin.site.register(Notification, NotificationAdmin)
