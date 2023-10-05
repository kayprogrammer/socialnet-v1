from django.contrib import admin
from apps.accounts.models import User

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

    readonly_fields = ("receivers", "read_by", "ntype", "comment", "reply", "sender")

    def save_model(self, request, obj, form, change):
        obj.ntype = "ADMIN"
        obj.host = request.get_host()
        obj.secured = request.is_secure()
        super().save_model(request, obj, form, change)


admin.site.register(Friend, FriendAdmin)
admin.site.register(Notification, NotificationAdmin)
