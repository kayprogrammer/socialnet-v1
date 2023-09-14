from django.contrib import admin

from apps.chat.models import Chat

# Register your models here.


class ChatAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "ctype", "created_at", "updated_at")
    list_filter = ("name", "owner", "ctype", "created_at", "updated_at")


admin.site.register(Chat, ChatAdmin)
