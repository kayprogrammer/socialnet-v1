import asyncio
from django.contrib import admin
from django.http.request import HttpRequest

from apps.profiles.models import Friend, Notification
from apps.profiles.utils import send_notification_in_socket


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

    readonly_fields = ("receivers", "read_by", "ntype", "comment", "reply", "sender")

    def save_model(self, request, obj, form, change):
        obj.from_admin_site = True
        obj.ntype = "ADMIN"
        obj.host = request.get_host()
        obj.secured = request.is_secure()
        super().save_model(request, obj, form, change)

    def delete_model(self, request: HttpRequest, obj: Notification) -> None:
        # Send socket notification
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(
            send_notification_in_socket(
                request.is_secure(), request.get_host(), obj, status="DELETED"
            )
        )
        super().delete_model(request, obj)


admin.site.register(Friend, FriendAdmin)
admin.site.register(Notification, NotificationAdmin)
