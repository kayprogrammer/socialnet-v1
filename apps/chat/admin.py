from django.contrib import admin

from apps.chat.models import Chat, Message

# Register your models here.


class ChatAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "ctype", "created_at", "updated_at")
    list_filter = ("name", "owner", "ctype", "created_at", "updated_at")


class MessageAdmin(admin.ModelAdmin):
    list_display = ("chat", "sender", "text", "file", "updated_at")
    list_filter = ("chat", "sender", "text", "file", "updated_at")


admin.site.register(Chat, ChatAdmin)
admin.site.register(Message, MessageAdmin)
